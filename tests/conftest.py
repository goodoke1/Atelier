"""Shared pytest fixtures.

All tests run against the deterministic offline stub provider and a temp SQLite
database, so the suite needs no API keys and no network.
"""
import io
import os
import sys

import pytest

# Make the backend importable and force stub mode before anything loads config.
BACKEND = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "app", "backend")
)
sys.path.insert(0, BACKEND)
os.environ["FASHION_AI_STUB"] = "1"


@pytest.fixture
def temp_env(tmp_path, monkeypatch):
    """Point the app at a throwaway DB + uploads dir for this test."""
    db = tmp_path / "test.db"
    uploads = tmp_path / "uploads"
    uploads.mkdir()
    monkeypatch.setenv("FASHION_AI_DB", str(db))
    monkeypatch.setenv("FASHION_AI_UPLOADS", str(uploads))

    # Reload config + modules so they pick up the patched env.
    import importlib

    import config
    importlib.reload(config)
    import database
    importlib.reload(database)
    import query
    importlib.reload(query)
    import providers.factory as factory
    factory.reset_provider()

    database.init_db()
    return {"db": str(db), "uploads": str(uploads)}


def make_jpeg(color=(120, 80, 60), size=(64, 64)) -> bytes:
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, "JPEG")
    return buf.getvalue()


@pytest.fixture
def client(temp_env):
    """A FastAPI TestClient with lifespan (DB init) active."""
    import importlib

    import main
    importlib.reload(main)
    from fastapi.testclient import TestClient

    with TestClient(main.app) as c:
        yield c


def seed_image(conn, **overrides):
    """Insert a classified image row directly (bypassing the model) for tests."""
    defaults = dict(
        filename="seed.jpg",
        original_filename="seed.jpg",
        status="classified",
        description="A seeded garment.",
        garment_type="dress",
        style="casual",
        material="cotton",
        color_palette="black, white",
        pattern="solid",
        season="spring/summer",
        occasion="casual",
        consumer_profile="young professional",
        trend_notes="minimalism",
        location_continent="Asia",
        location_country="Japan",
        location_city="Tokyo",
        designer="Aiko",
        image_year=2024,
        image_month=5,
    )
    defaults.update(overrides)
    cols = ", ".join(defaults.keys())
    placeholders = ", ".join("?" for _ in defaults)
    cur = conn.execute(
        f"INSERT INTO images ({cols}) VALUES ({placeholders})", list(defaults.values())
    )
    image_id = cur.lastrowid
    from database import reindex_image

    reindex_image(conn, image_id)
    return image_id
