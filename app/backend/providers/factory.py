"""Select and build the active classification provider from config."""
import config
from .base import ImageClassificationProvider
from .stub_provider import StubProvider

_cached: ImageClassificationProvider = None

def _build() -> ImageClassificationProvider:
    # Default to the offline stub provider for initial prototyping and offline testing
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
