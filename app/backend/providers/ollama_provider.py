"""Local Ollama (e.g. LLaVA) vision provider — no API key required."""
import httpx

from .base import ImageClassificationProvider, to_base64
from .prompt import CLASSIFICATION_PROMPT


class OllamaProvider(ImageClassificationProvider):
    name = "ollama"

    def __init__(self, host: str, model: str):
        self.host = host.rstrip("/")
        self.model = model

    def classify(self, image_bytes: bytes, media_type: str) -> str:
        response = httpx.post(
            f"{self.host}/api/generate",
            json={
                "model": self.model,
                "prompt": CLASSIFICATION_PROMPT,
                "images": [to_base64(image_bytes)],
                "stream": False,
            },
            timeout=180,
        )
        response.raise_for_status()
        return response.json().get("response", "")
