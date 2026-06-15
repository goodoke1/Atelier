"""Integration tests for filter behaviour, with emphasis on location & time.

These exercise the real query builder + SQLite (FTS included) against seeded
data, then also hit the HTTP /api/images and /api/filters endpoints to confirm
the wiring end to end.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app", "backend")))

from conftest import seed_image  # noqa: E402


def _run(temp_env, params):
    """Execute the listing query directly against the DB and return rows."""
    import database
    from query import build_image_query

    list_cols = {"style", "material", "color_palette", "trend_notes"}
    sql, args = build_image_query(params, list_columns=list_cols)
    with database.get_db() as conn:
        return conn.execute(sql, args).fetchall()


def test_filter_by_location_country(temp_env):
    import database

    with database.get_db() as conn:
        seed_image(conn, location_country="Japan", location_city="Tokyo")
        seed_image(conn, location_country="France", location_city="Paris")
        seed_image(conn, location_country="Japan", location_city="Osaka")

    rows = _run(temp_env, {"location_country": ["Japan"]})
    assert len(rows) == 2
    assert {r["location_city"] for r in rows} == {"Tokyo", "Osaka"}


def test_filter_by_continent_and_city_together(temp_env):
    import database

    with database.get_db() as conn:
        seed_image(conn, location_continent="Asia", location_city="Tokyo")
        seed_image(conn, location_continent="Asia", location_city="Seoul")
        seed_image(conn, location_continent="Europe", location_city="Paris")

    # Continent + city AND-ed across fields.
    rows = _run(temp_env, {"location_continent": ["Asia"], "location_city": ["Seoul"]})
    assert len(rows) == 1
    assert rows[0]["location_city"] == "Seoul"


def test_filter_by_year_and_month(temp_env):
    import database

    with database.get_db() as conn:
        seed_image(conn, image_year=2024, image_month=5)
        seed_image(conn, image_year=2024, image_month=11)
        seed_image(conn, image_year=2023, image_month=5)

    assert len(_run(temp_env, {"image_year": ["2024"]})) == 2
    assert len(_run(temp_env, {"image_year": ["2024"], "image_month": ["5"]})) == 1
    assert len(_run(temp_env, {"image_month": ["5"]})) == 2


def test_multiple_values_for_one_field_are_ored(temp_env):
    import database

    with database.get_db() as conn:
        seed_image(conn, garment_type="dress")
        seed_image(conn, garment_type="jacket")
        seed_image(conn, garment_type="coat")

    rows = _run(temp_env, {"garment_type": ["dress", "coat"]})
    assert {r["garment_type"] for r in rows} == {"dress", "coat"}


def test_list_column_substring_match(temp_env):
    import database

    with database.get_db() as conn:
        seed_image(conn, color_palette="black, white")
        seed_image(conn, color_palette="red, blue")

    # "white" should match the comma-separated "black, white".
    rows = _run(temp_env, {"color_palette": ["white"]})
    assert len(rows) == 1


def test_full_text_search_matches_description_and_annotations(temp_env):
    import database

    with database.get_db() as conn:
        i1 = seed_image(conn, description="An embroidered neckline with artisan detail.")
        seed_image(conn, description="A plain athletic tank.")
        # Annotation text becomes searchable after reindex.
        conn.execute(
            "INSERT INTO annotations (image_id, tag, note) VALUES (?, ?, ?)",
            (i1, "market", "found at an artisan market"),
        )
        database.reindex_image(conn, i1)

    assert len(_run(temp_env, {"q": ["embroidered"]})) == 1
    assert len(_run(temp_env, {"q": ["artisan market"]})) == 1
    assert len(_run(temp_env, {"q": ["athletic"]})) == 1


def test_dynamic_filters_endpoint(client):
    """Filters are generated from data, not hardcoded, and split list columns."""
    import database

    with database.get_db() as conn:
        seed_image(conn, garment_type="dress", color_palette="black, white", location_country="Japan")
        seed_image(conn, garment_type="dress", color_palette="black", location_country="France")
        seed_image(conn, garment_type="jacket", color_palette="red", location_country="Japan")

    data = client.get("/api/filters").json()["filters"]
    # garment_type facet: dress (2) before jacket (1), frequency-sorted.
    gt = {o["value"]: o["count"] for o in data["garment_type"]}
    assert gt == {"dress": 2, "jacket": 1}
    # color_palette split out of comma lists: black appears in 2 images.
    cp = {o["value"]: o["count"] for o in data["color_palette"]}
    assert cp["black"] == 2
    # location facet present and dynamic.
    assert {o["value"] for o in data["location_country"]} == {"Japan", "France"}


def test_images_endpoint_combined_filters(client):
    import database

    with database.get_db() as conn:
        seed_image(conn, garment_type="dress", location_country="Japan", image_year=2024)
        seed_image(conn, garment_type="dress", location_country="Japan", image_year=2023)
        seed_image(conn, garment_type="jacket", location_country="Japan", image_year=2024)

    resp = client.get("/api/images", params={"garment_type": "dress", "image_year": "2024"})
    body = resp.json()
    assert body["count"] == 1
    assert body["images"][0]["garment_type"] == "dress"
    assert body["images"][0]["image_year"] == 2024
