"""End-to-end tests over the HTTP API.

Covers the core workflow the case study asks for: upload -> classify -> filter,
plus annotation search and deletion. Runs against the stub provider so the
"classification" is deterministic and offline, but exercises every layer
(routes, background task, DB, FTS).
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app", "backend")))

from conftest import make_jpeg  # noqa: E402


def _upload(client, color, **context):
    files = {"file": ("shot.jpg", make_jpeg(color), "image/jpeg")}
    resp = client.post("/api/images/upload", files=files, data=context)
    assert resp.status_code == 202
    return resp.json()["id"]


def test_health(client):
    body = client.get("/api/health").json()
    assert body["status"] == "ok"
    assert body["provider"] == "stub"


def test_upload_classify_filter_workflow(client):
    # Upload with location + time context.
    image_id = _upload(
        client,
        (200, 30, 30),
        location_continent="Asia",
        location_country="Japan",
        location_city="Tokyo",
        designer="Aiko",
        image_year="2024",
        image_month="5",
    )

    # The background task runs synchronously after the response in TestClient,
    # so by the time we GET the image it is classified.
    detail = client.get(f"/api/images/{image_id}").json()
    assert detail["status"] == "classified"
    assert detail["garment_type"]  # stub always fills attributes
    assert detail["description"]

    # It now appears in the library and contributes to dynamic filters.
    assert client.get("/api/images").json()["count"] == 1
    filters = client.get("/api/filters").json()["filters"]
    assert "garment_type" in filters
    assert filters["location_country"][0]["value"] == "Japan"

    # Filtering by the supplied location + time returns it.
    assert client.get("/api/images", params={"location_country": "Japan"}).json()["count"] == 1
    assert client.get("/api/images", params={"image_year": "2024"}).json()["count"] == 1
    # A non-matching filter excludes it.
    assert client.get("/api/images", params={"location_country": "France"}).json()["count"] == 0


def test_annotation_is_searchable_and_distinct(client):
    image_id = _upload(client, (40, 90, 160))

    # Add a designer annotation.
    resp = client.post(
        f"/api/images/{image_id}/annotations",
        json={"tag": "favourite", "note": "embroidered neckline detail"},
    )
    assert resp.status_code == 201

    # The annotation comes back attached to the image, separate from AI fields.
    detail = client.get(f"/api/images/{image_id}").json()
    assert len(detail["annotations"]) == 1
    assert detail["annotations"][0]["tag"] == "favourite"

    # It is searchable via full-text search.
    found = client.get("/api/search", params={"q": "embroidered"}).json()
    assert found["count"] == 1
    assert found["images"][0]["id"] == image_id


def test_delete_image_removes_it_everywhere(client):
    image_id = _upload(client, (10, 10, 10))
    assert client.get("/api/images").json()["count"] == 1

    assert client.delete(f"/api/images/{image_id}").status_code == 204
    assert client.get("/api/images").json()["count"] == 0
    assert client.get(f"/api/images/{image_id}").status_code == 404
    # Removed from the search index too.
    assert client.get("/api/search", params={"q": "garment"}).json()["count"] == 0


def test_rejects_unsupported_file_type(client):
    files = {"file": ("notes.txt", b"hello", "text/plain")}
    resp = client.post("/api/images/upload", files=files)
    assert resp.status_code == 400
