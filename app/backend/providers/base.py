"""Provider abstraction + shared image helpers."""
import base64
import io
from abc import ABC, abstractmethod
from typing import Tuple

from PIL import Image


class ImageClassificationProvider(ABC):
    """A multimodal model that turns an image into raw classification text."""

    name: str = "base"

    @abstractmethod
    def classify(self, image_bytes: bytes, media_type: str) -> str:
        """Return raw model text (parsed downstream by parser.parse_classification)."""
        raise NotImplementedError


def load_image_bytes(filepath: str, max_dim: int = 1024) -> Tuple[bytes, str]:
    """Read an image, downscale it for cheaper/faster inference, return (bytes, media_type).

    Large field photos waste tokens; 1024px on the long edge is plenty for
    garment classification. Always re-encoded as JPEG for a predictable media type.
    """
    with Image.open(filepath) as img:
        img = img.convert("RGB")
        img.thumbnail((max_dim, max_dim))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=88)
        return buf.getvalue(), "image/jpeg"


def to_base64(image_bytes: bytes) -> str:
    return base64.standard_b64encode(image_bytes).decode("utf-8")
