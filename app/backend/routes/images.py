"""Image upload, listing, detail, file serving, and deletion."""
import os
import uuid
from typing import Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.responses import FileResponse

import config
from classifier import classify_image
from database import ATTRIBUTE_COLUMNS, CONTEXT_COLUMNS, get_db, reindex_image
from query import build_image_query

router = APIRouter(prefix="/api/images", tags=["images"])

# Attribute columns that hold comma-separated lists, so filters match as substrings.
LIST_COLUMNS = {"style", "material", "color_palette", "trend_notes"}


def _row_to_dict(row) -> dict:
    return {k: row[k] for k in row.keys()}


def _attach_annotations(conn, image: dict) -> dict:
    rows = conn.execute(
        "SELECT * FROM annotations WHERE image_id = ? ORDER BY created_at DESC",
        (image["id"],),
    ).fetchall()
    image["annotations"] = [_row_to_dict(r) for r in rows]
    return image


def _classify_in_background(image_id: int, filepath: str) -> None:
    """Run classification and persist results. Marks failed on any error."""
    with get_db() as conn:
        conn.execute("UPDATE images SET status = 'processing' WHERE id = ?", (image_id,))

    try:
        result = classify_image(filepath)
        attrs = result["attributes"]
        with get_db() as conn:
            conn.execute(
                f"""
                UPDATE images SET
                    status = 'classified',
                    description = ?,
                    {", ".join(f"{c} = ?" for c in ATTRIBUTE_COLUMNS)}
                WHERE id = ?
                """,
                [result["description"], *[attrs.get(c) for c in ATTRIBUTE_COLUMNS], image_id],
            )
            reindex_image(conn, image_id)
    except Exception as exc:  # noqa: BLE001 - surface any provider error to the user
        with get_db() as conn:
            conn.execute(
                "UPDATE images SET status = 'failed', error_message = ? WHERE id = ?",
                (str(exc)[:500], image_id),
            )


@router.post("/upload", status_code=202)
async def upload_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    location_continent: Optional[str] = Form(None),
    location_country: Optional[str] = Form(None),
    location_city: Optional[str] = Form(None),
    designer: Optional[str] = Form(None),
    image_year: Optional[int] = Form(None),
    image_month: Optional[int] = Form(None),
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in config.ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type '{ext}'.")

    contents = await file.read()
    if len(contents) > config.MAX_UPLOAD_BYTES:
        raise HTTPException(400, "File too large (max 15 MB).")

    os.makedirs(config.UPLOAD_DIR, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(config.UPLOAD_DIR, stored_name)
    with open(filepath, "wb") as fh:
        fh.write(contents)

    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO images
                (filename, original_filename, status,
                 location_continent, location_country, location_city,
                 designer, image_year, image_month)
            VALUES (?, ?, 'pending', ?, ?, ?, ?, ?, ?)
            """,
            (
                stored_name,
                file.filename,
                location_continent,
                location_country,
                location_city,
                designer,
                image_year,
                image_month,
            ),
        )
        image_id = cur.lastrowid

    background_tasks.add_task(_classify_in_background, image_id, filepath)
    return {"id": image_id, "status": "pending"}


@router.get("")
def list_images(request: Request):
    """List images, dynamically filtered by any attribute/context query params.

    Recognised params: every attribute & context column, plus ``q`` (full-text
    search), ``status``, ``limit``, ``offset``. Repeated params OR within a field
    and AND across fields. List-valued columns match as substrings.
    """
    params = request.query_params
    sql, args = build_image_query(params, list_columns=LIST_COLUMNS)
    with get_db() as conn:
        rows = conn.execute(sql, args).fetchall()
        images = [_attach_annotations(conn, _row_to_dict(r)) for r in rows]
    return {"images": images, "count": len(images)}


@router.get("/{image_id}")
def get_image(image_id: int):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM images WHERE id = ?", (image_id,)).fetchone()
        if row is None:
            raise HTTPException(404, "Image not found.")
        return _attach_annotations(conn, _row_to_dict(row))


@router.get("/{image_id}/file")
def get_image_file(image_id: int):
    with get_db() as conn:
        row = conn.execute("SELECT filename FROM images WHERE id = ?", (image_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "Image not found.")
    path = os.path.join(config.UPLOAD_DIR, row["filename"])
    if not os.path.exists(path):
        raise HTTPException(404, "Image file missing.")
    return FileResponse(path)


@router.delete("/{image_id}", status_code=204)
def delete_image(image_id: int):
    with get_db() as conn:
        row = conn.execute("SELECT filename FROM images WHERE id = ?", (image_id,)).fetchone()
        if row is None:
            raise HTTPException(404, "Image not found.")
        conn.execute("DELETE FROM images_fts WHERE image_id = ?", (image_id,))
        conn.execute("DELETE FROM images WHERE id = ?", (image_id,))
    path = os.path.join(config.UPLOAD_DIR, row["filename"])
    if os.path.exists(path):
        os.remove(path)
    return None
