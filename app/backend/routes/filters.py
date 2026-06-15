"""Dynamically generated filter options derived from the data itself."""
from fastapi import APIRouter

from database import ATTRIBUTE_COLUMNS, CONTEXT_COLUMNS, get_db

router = APIRouter(prefix="/api/filters", tags=["filters"])

# Columns whose values are comma-separated lists need splitting into options.
_LIST_COLUMNS = {"style", "material", "color_palette", "trend_notes"}


def _split(value: str):
    return [p.strip() for p in value.split(",") if p.strip()]


@router.get("")
def get_filters():
    """Return available filter options for every facet, computed from DISTINCT data.

    Options are sorted by frequency (most common first) so the UI surfaces the
    most useful filters. Nothing here is hardcoded — empty facets simply omit.
    """
    facets = {}
    with get_db() as conn:
        for col in ATTRIBUTE_COLUMNS + CONTEXT_COLUMNS:
            rows = conn.execute(
                f"SELECT {col} AS v FROM images "
                f"WHERE {col} IS NOT NULL AND TRIM({col}) != '' AND status = 'classified'"
            ).fetchall()

            counts = {}
            for r in rows:
                raw = r["v"]
                parts = _split(str(raw)) if col in _LIST_COLUMNS else [str(raw).strip()]
                for p in parts:
                    counts[p] = counts.get(p, 0) + 1

            if counts:
                ordered = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0].lower()))
                facets[col] = [{"value": v, "count": c} for v, c in ordered]

    return {"filters": facets}
