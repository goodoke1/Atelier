"""Anthropic Claude vision provider."""
from .base import ImageClassificationProvider, to_base64
from .prompt import CLASSIFICATION_PROMPT


class ClaudeProvider(ImageClassificationProvider):
    name = "claude"

    def __init__(self, api_key: str, model: str):
        import anthropic

        self.model = model
        self.client = anthropic.Anthropic(api_key=api_key)

    def classify(self, image_bytes: bytes, media_type: str) -> str:
        message = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": to_base64(image_bytes),
                            },
                        },
                        {"type": "text", "text": CLASSIFICATION_PROMPT},
                    ],
                }
            ],
        )
        return "".join(block.text for block in message.content if block.type == "text")
