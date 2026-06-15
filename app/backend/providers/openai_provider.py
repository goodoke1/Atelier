"""OpenAI GPT-4o vision provider."""
from .base import ImageClassificationProvider, to_base64
from .prompt import CLASSIFICATION_PROMPT


class OpenAIProvider(ImageClassificationProvider):
    name = "openai"

    def __init__(self, api_key: str, model: str):
        from openai import OpenAI

        self.model = model
        self.client = OpenAI(api_key=api_key)

    def classify(self, image_bytes: bytes, media_type: str) -> str:
        data_uri = f"data:{media_type};base64,{to_base64(image_bytes)}"
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": CLASSIFICATION_PROMPT},
                        {"type": "image_url", "image_url": {"url": data_uri}},
                    ],
                }
            ],
        )
        return response.choices[0].message.content or ""
