"""Deterministic offline provider.

Used when no API key is configured (FASHION_AI_STUB) so the full upload ->
classify -> filter -> search workflow works in demos and tests without any
network calls. It derives plausible-but-fake attributes from the image bytes so
different images get different (stable) labels.
"""
import hashlib

from .base import ImageClassificationProvider

_GARMENTS = ["dress", "jacket", "top", "trousers", "skirt", "knitwear", "coat", "jumpsuit"]
_STYLES = ["streetwear", "minimalist", "bohemian", "formal", "vintage", "sporty"]
_MATERIALS = ["cotton", "denim", "silk", "wool", "leather", "linen"]
_PATTERNS = ["solid", "striped", "floral", "geometric", "plaid", "abstract"]
_SEASONS = ["spring/summer", "fall/winter", "transitional"]
_OCCASIONS = ["casual", "office", "evening", "outdoor", "resort", "athletic"]
_PROFILES = ["young professional", "teen", "luxury", "streetwear enthusiast", "mature"]
_TRENDS = ["oversized silhouettes", "quiet luxury", "Y2K revival", "utility chic", "monochrome"]
_COLORS = ["black", "white", "navy", "beige", "olive", "burgundy", "rust", "cream"]


def _pick(seq, h, salt):
    return seq[int(hashlib.sha256((h + salt).encode()).hexdigest(), 16) % len(seq)]


class StubProvider(ImageClassificationProvider):
    name = "stub"

    def classify(self, image_bytes: bytes, media_type: str) -> str:
        h = hashlib.sha256(image_bytes).hexdigest()
        garment = _pick(_GARMENTS, h, "g")
        style = _pick(_STYLES, h, "s")
        c1, c2 = _pick(_COLORS, h, "c1"), _pick(_COLORS, h, "c2")
        return (
            f"DESCRIPTION: A {style} {garment} with clean lines and a considered "
            f"silhouette, photographed as field inspiration. The piece reads as "
            f"{c1} and {c2} with thoughtful detailing.\n"
            "ATTRIBUTES: {"
            f'"garment_type": "{garment}", '
            f'"style": "{style}", '
            f'"material": "{_pick(_MATERIALS, h, "m")}", '
            f'"color_palette": "{c1}, {c2}", '
            f'"pattern": "{_pick(_PATTERNS, h, "p")}", '
            f'"season": "{_pick(_SEASONS, h, "se")}", '
            f'"occasion": "{_pick(_OCCASIONS, h, "o")}", '
            f'"consumer_profile": "{_pick(_PROFILES, h, "cp")}", '
            f'"trend_notes": "{_pick(_TRENDS, h, "t")}"'
            "}"
        )
