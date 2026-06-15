"""Parse raw multimodal model output into a description + structured attributes.

The model is asked to reply in the form::

    DESCRIPTION: <text>
    ATTRIBUTES: { ...json... }

but models are not perfectly obedient, so this parser is deliberately tolerant:
it copes with markdown code fences, missing labels, extra prose, and malformed
JSON, always returning a predictable dict shape. This module has no I/O and is
the primary target of the parser unit tests.
"""
import json
import re
from typing import Any, Dict

# The structured fields we expect. Anything else the model returns is dropped;
# anything missing is filled with None so downstream code can rely on the keys.
EXPECTED_ATTRIBUTES = [
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


def _strip_code_fences(text: str) -> str:
    """Remove ```json ... ``` (or plain ```) fences around a JSON block."""
    text = text.strip()
    fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
    if fence:
        return fence.group(1).strip()
    return text


def _extract_first_json_object(text: str) -> str:
    """Return the substring spanning the first balanced {...} object, or ''.

    Handles nested braces and braces inside strings so we don't truncate on a
    `{` that appears inside a value.
    """
    start = text.find("{")
    if start == -1:
        return ""
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]
    return ""


def _normalize_attributes(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Coerce attribute values to clean strings and keep only expected keys."""
    out: Dict[str, Any] = {}
    for key in EXPECTED_ATTRIBUTES:
        value = raw.get(key)
        if value is None:
            out[key] = None
        elif isinstance(value, list):
            out[key] = ", ".join(str(v).strip() for v in value if str(v).strip())
        else:
            out[key] = str(value).strip() or None
    return out


def parse_classification(text: str) -> Dict[str, Any]:
    """Parse raw model text into ``{"description": str, "attributes": dict}``.

    Always returns the two keys. ``attributes`` always contains every expected
    field (value None when the model omitted or mangled it).
    """
    if not text or not text.strip():
        return {"description": "", "attributes": _normalize_attributes({})}

    text = text.strip()

    # Split on the ATTRIBUTES label if present; otherwise treat the whole thing
    # as description and try to find an embedded JSON object.
    desc_match = re.search(r"DESCRIPTION:\s*(.*?)(?:\n\s*ATTRIBUTES:|$)", text, re.DOTALL | re.IGNORECASE)
    attr_match = re.search(r"ATTRIBUTES:\s*(.*)$", text, re.DOTALL | re.IGNORECASE)

    if desc_match:
        description = desc_match.group(1).strip()
    else:
        # No explicit label: description is everything before the first JSON brace.
        brace = text.find("{")
        description = (text[:brace] if brace != -1 else text).strip()
        description = re.sub(r"^DESCRIPTION:\s*", "", description, flags=re.IGNORECASE).strip()

    attr_blob = attr_match.group(1) if attr_match else text
    attr_blob = _strip_code_fences(attr_blob)
    json_str = _extract_first_json_object(attr_blob)

    attributes: Dict[str, Any] = {}
    if json_str:
        try:
            parsed = json.loads(json_str)
            if isinstance(parsed, dict):
                attributes = parsed
        except json.JSONDecodeError:
            attributes = {}

    return {
        "description": description,
        "attributes": _normalize_attributes(attributes),
    }
