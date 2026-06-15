"""Build the dynamic image-listing SQL from query parameters.

Separated from the route so the filtering logic (the trickiest part, especially
location + time filters) can be unit/integration tested without a web server.
"""
from typing import Iterable, List, Set, Tuple

from database import ATTRIBUTE_COLUMNS, CONTEXT_COLUMNS

# Every column a caller is allowed to filter on.
FILTERABLE_COLUMNS = set(ATTRIBUTE_COLUMNS) | set(CONTEXT_COLUMNS) | {"status"}
INT_COLUMNS = {"image_year", "image_month"}


def build_image_query(params, list_columns: Set[str] = frozenset()) -> Tuple[str, List]:
    """Return (sql, args) for a filtered, optionally full-text-searched listing.

    ``params`` is anything supporting ``.getlist(key)`` and iteration over keys
    (Starlette QueryParams or a plain dict-of-lists). Repeated values for one
    field are OR-ed together; different fields are AND-ed.
    """
    where: List[str] = []
    args: List = []

    # Optional full-text search via the FTS table.
    q = _first(params, "q")
    base = "SELECT images.* FROM images"
    if q and q.strip():
        base += " JOIN images_fts ON images_fts.image_id = images.id"
        where.append("images_fts MATCH ?")
        args.append(_fts_query(q))

    keys = params.keys() if hasattr(params, "keys") else params
    for key in set(keys):
        if key not in FILTERABLE_COLUMNS:
            continue
        values = [v for v in _getlist(params, key) if v not in (None, "")]
        if not values:
            continue

        clauses = []
        if key in list_columns:
            # Substring match (case-insensitive) for comma-separated list columns.
            for v in values:
                clauses.append(f"LOWER(images.{key}) LIKE ?")
                args.append(f"%{v.lower()}%")
        elif key in INT_COLUMNS:
            for v in values:
                clauses.append(f"images.{key} = ?")
                args.append(int(v))
        else:
            for v in values:
                clauses.append(f"LOWER(images.{key}) = ?")
                args.append(v.lower())
        where.append("(" + " OR ".join(clauses) + ")")

    sql = base
    if where:
        sql += " WHERE " + " AND ".join(where)

    # FTS join already orders by rank; otherwise newest first.
    if not (q and q.strip()):
        sql += " ORDER BY images.uploaded_at DESC, images.id DESC"

    limit = int(_first(params, "limit") or 200)
    offset = int(_first(params, "offset") or 0)
    sql += " LIMIT ? OFFSET ?"
    args.extend([min(limit, 500), offset])
    return sql, args


def _fts_query(raw: str) -> str:
    """Turn a user phrase into a forgiving FTS5 query (prefix match per term)."""
    terms = [t for t in _sanitize(raw).split() if t]
    if not terms:
        return '""'
    return " ".join(f'{t}*' for t in terms)


def _sanitize(raw: str) -> str:
    # Drop FTS operator characters so user input can't break the MATCH syntax.
    return "".join(c if c.isalnum() or c.isspace() else " " for c in raw)


def _getlist(params, key) -> Iterable[str]:
    if hasattr(params, "getlist"):
        return params.getlist(key)
    val = params.get(key)
    if val is None:
        return []
    return val if isinstance(val, list) else [val]


def _first(params, key):
    vals = list(_getlist(params, key))
    return vals[0] if vals else None
