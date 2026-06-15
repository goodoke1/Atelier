"""Designer annotations: user-supplied tags/notes layered over AI metadata."""
from fastapi import APIRouter, HTTPException

from database import get_db, reindex_image
from models import AnnotationCreate

router = APIRouter(prefix="/api", tags=["annotations"])


@router.post("/images/{image_id}/annotations", status_code=201)
def add_annotation(image_id: int, body: AnnotationCreate):
    if not (body.tag or body.note):
        raise HTTPException(400, "Provide at least a tag or a note.")
    with get_db() as conn:
        exists = conn.execute("SELECT 1 FROM images WHERE id = ?", (image_id,)).fetchone()
        if not exists:
            raise HTTPException(404, "Image not found.")
        cur = conn.execute(
            "INSERT INTO annotations (image_id, tag, note) VALUES (?, ?, ?)",
            (image_id, body.tag, body.note),
        )
        # Re-index so the new annotation becomes searchable immediately.
        reindex_image(conn, image_id)
        row = conn.execute(
            "SELECT * FROM annotations WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
    return {k: row[k] for k in row.keys()}


@router.get("/images/{image_id}/annotations")
def list_annotations(image_id: int):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM annotations WHERE image_id = ? ORDER BY created_at DESC",
            (image_id,),
        ).fetchall()
    return {"annotations": [{k: r[k] for k in r.keys()} for r in rows]}


@router.delete("/annotations/{annotation_id}", status_code=204)
def delete_annotation(annotation_id: int):
    with get_db() as conn:
        row = conn.execute(
            "SELECT image_id FROM annotations WHERE id = ?", (annotation_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(404, "Annotation not found.")
        conn.execute("DELETE FROM annotations WHERE id = ?", (annotation_id,))
        reindex_image(conn, row["image_id"])
    return None
