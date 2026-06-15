"""Full-text search endpoint (delegates to the same FTS-backed query builder)."""
from fastapi import APIRouter, Query

from database import get_db
from query import build_image_query

router = APIRouter(prefix="/api/search", tags=["search"])

_LIST_COLUMNS = {"style", "material", "color_palette", "trend_notes"}


@router.get("")
def search(q: str = Query(..., min_length=1)):
    sql, args = build_image_query({"q": [q]}, list_columns=_LIST_COLUMNS)
    with get_db() as conn:
        rows = conn.execute(sql, args).fetchall()
        images = [{k: r[k] for k in r.keys()} for r in rows]
    return {"images": images, "count": len(images), "query": q}
