"""Unit tests for parsing model output into structured attributes.

The parser is the contract between the (unreliable) LLM text and the structured
DB columns, so it gets the most thorough coverage: happy path, code fences,
missing labels, malformed JSON, list coercion, and empty input.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app", "backend")))

from parser import EXPECTED_ATTRIBUTES, parse_classification  # noqa: E402


def test_happy_path():
    text = (
        "DESCRIPTION: A tailored wool coat with a relaxed shoulder.\n"
        'ATTRIBUTES: {"garment_type": "coat", "style": "minimalist", '
        '"material": "wool", "color_palette": "camel, black", "pattern": "solid", '
        '"season": "fall/winter", "occasion": "office", '
        '"consumer_profile": "young professional", "trend_notes": "quiet luxury"}'
    )
    result = parse_classification(text)
    assert "tailored wool coat" in result["description"]
    attrs = result["attributes"]
    assert attrs["garment_type"] == "coat"
    assert attrs["color_palette"] == "camel, black"
    assert attrs["trend_notes"] == "quiet luxury"


def test_all_expected_keys_present():
    result = parse_classification('DESCRIPTION: x\nATTRIBUTES: {"garment_type": "top"}')
    for key in EXPECTED_ATTRIBUTES:
        assert key in result["attributes"]
    # Missing fields are None, not absent.
    assert result["attributes"]["style"] is None


def test_strips_markdown_code_fences():
    text = (
        "DESCRIPTION: A denim jacket.\n"
        "ATTRIBUTES: ```json\n"
        '{"garment_type": "jacket", "material": "denim"}\n'
        "```"
    )
    result = parse_classification(text)
    assert result["attributes"]["garment_type"] == "jacket"
    assert result["attributes"]["material"] == "denim"


def test_handles_malformed_json_gracefully():
    text = "DESCRIPTION: A skirt.\nATTRIBUTES: {garment_type: skirt, oops}"
    result = parse_classification(text)
    # Description survives; attributes default to all-None without raising.
    assert "skirt" in result["description"].lower()
    assert all(v is None for v in result["attributes"].values())


def test_coerces_list_values_to_csv():
    text = 'DESCRIPTION: x\nATTRIBUTES: {"style": ["boho", "casual"], "color_palette": ["red", "blue"]}'
    result = parse_classification(text)
    assert result["attributes"]["style"] == "boho, casual"
    assert result["attributes"]["color_palette"] == "red, blue"


def test_no_attributes_label_finds_embedded_json():
    text = 'A loose linen shirt. {"garment_type": "shirt", "material": "linen"}'
    result = parse_classification(text)
    assert result["attributes"]["garment_type"] == "shirt"
    assert "loose linen shirt" in result["description"]


def test_nested_braces_in_values():
    text = 'DESCRIPTION: x\nATTRIBUTES: {"trend_notes": "logo {motif} revival", "garment_type": "top"}'
    result = parse_classification(text)
    assert result["attributes"]["garment_type"] == "top"
    assert "revival" in result["attributes"]["trend_notes"]


def test_empty_input():
    result = parse_classification("")
    assert result["description"] == ""
    assert all(v is None for v in result["attributes"].values())


def test_extra_whitespace_and_casing():
    text = "  description:   A red dress.  \n  ATTRIBUTES:  {\"garment_type\":\"dress\"}  "
    result = parse_classification(text)
    assert result["attributes"]["garment_type"] == "dress"
    assert "red dress" in result["description"]
