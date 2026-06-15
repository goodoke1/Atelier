"""Select and build the active classification provider from config."""
import config
from .base import ImageClassificationProvider
from .stub_provider import StubProvider

_cached: ImageClassificationProvider = None

def _build() -> ImageClassificationProvider:
    # Explicit stub mode, or any provider missing its credentials, falls back
    # to the deterministic offline stub so the app always works.
    if config.STUB_MODE:
        return StubProvider()

    provider = config.MODEL_PROVIDER

    if provider == "claude":
        if not config.ANTHROPIC_API_KEY:
            return StubProvider()
        from .claude_provider import ClaudeProvider
        return ClaudeProvider(config.ANTHROPIC_API_KEY, config.CLAUDE_MODEL)

    if provider == "openai":
        if not config.OPENAI_API_KEY:
            return StubProvider()
        from .openai_provider import OpenAIProvider
        return OpenAIProvider(config.OPENAI_API_KEY, config.OPENAI_MODEL)

    if provider == "ollama":
        from .ollama_provider import OllamaProvider
        return OllamaProvider(config.OLLAMA_HOST, config.OLLAMA_MODEL)

    return StubProvider()

def get_provider() -> ImageClassificationProvider:
    global _cached
    if _cached is None:
        _cached = _build()
    return _cached

def reset_provider() -> None:
    """Clear the cached provider (used by tests)."""
    global _cached
    _cached = None
