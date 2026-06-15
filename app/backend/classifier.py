"""Glue: load an image file, run the active provider, parse the result."""
from typing import Any, Dict

from parser import parse_classification
from providers import get_provider
from providers.base import load_image_bytes


def classify_image(filepath: str) -> Dict[str, Any]:
    """Classify an image file into {"description", "attributes"}.

    Raises on provider/network errors so the caller can record a failed status.
    """
    image_bytes, media_type = load_image_bytes(filepath)
    raw = get_provider().classify(image_bytes, media_type)
    return parse_classification(raw)
