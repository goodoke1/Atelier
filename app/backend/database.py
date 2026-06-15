"""SQLite database layer with an FTS5 full-text index.

The schema stores one row per image with both the AI-generated description and
the structured attributes (flat columns so they're trivial to filter on). A
companion FTS5 virtual table powers natural-language search across descriptions,
key attributes, and designer annotations.
"""
import os
import sqlite3
from contextlib import contextmanager
from typing import Iterator

from config import DB_PATH

# Structured attribute columns produced by the classifier.
ATTRIBUTE_COLUMNS = [
    "garment_type",
    "style",
    "material",
    "color_palette",
    "pattern",
    "season",
    "occasion",
    "consumer_profile",
    "trend_notes",
]

# Contextual columns supplied by the user at upload time.
CONTEXT_COLUMNS = [
    "location_continent",
    "location_country",
    "location_city",
    "designer",
    "image_year",
    "image_month",
]


def _connect(path: str = None) -> sqlite3.Connection:
    path = path or DB_PATH
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


@contextmanager
def get_db(path: str = None) -> Iterator[sqlite3.Connection]:
    conn = _connect(path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(path: str = None) -> None:
    """Create tables and the FTS index if they don't already exist."""
    with get_db(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                original_filename TEXT,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT NOT NULL DEFAULT 'pending',
                error_message TEXT,
                description TEXT,
                garment_type TEXT,
                style TEXT,
                material TEXT,
                color_palette TEXT,
                pattern TEXT,
                season TEXT,
                occasion TEXT,
                consumer_profile TEXT,
                trend_notes TEXT,
                location_continent TEXT,
                location_country TEXT,
                location_city TEXT,
                designer TEXT,
                image_year INTEGER,
                image_month INTEGER
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS annotations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id INTEGER NOT NULL REFERENCES images(id) ON DELETE CASCADE,
                tag TEXT,
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # FTS5 index combining AI text and human annotations. We keep a single
        # row per image and rebuild it whenever the image or its annotations
        # change (see reindex_image).
        conn.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS images_fts USING fts5(
                image_id UNINDEXED,
                description,
                garment_type,
                style,
                material,
                trend_notes,
                annotation_text,
                tokenize = 'porter unicode61'
            )
            """
        )


def reindex_image(conn: sqlite3.Connection, image_id: int) -> None:
    """Rebuild the FTS row for one image from its current data + annotations."""
    row = conn.execute("SELECT * FROM images WHERE id = ?", (image_id,)).fetchone()
    if row is None:
        return
    ann_rows = conn.execute(
        "SELECT tag, note FROM annotations WHERE image_id = ?", (image_id,)
    ).fetchall()
    annotation_text = " ".join(
        " ".join(filter(None, (a["tag"], a["note"]))) for a in ann_rows
    )

    conn.execute("DELETE FROM images_fts WHERE image_id = ?", (image_id,))
    conn.execute(
        """
        INSERT INTO images_fts
            (image_id, description, garment_type, style, material, trend_notes, annotation_text)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            image_id,
            row["description"] or "",
            row["garment_type"] or "",
            row["style"] or "",
            row["material"] or "",
            row["trend_notes"] or "",
            annotation_text,
        ),
    )
