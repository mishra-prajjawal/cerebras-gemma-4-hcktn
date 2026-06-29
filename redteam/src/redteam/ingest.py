"""Document ingest: bounded text chunking. No model calls here."""
from __future__ import annotations

_MAX_CHARS = 12000  # bounded input per reviewer (NASA rule 3: no unbounded growth)


def clip(text: str) -> str:
    """Clamp document text to a safe size. Postcondition: len <= _MAX_CHARS."""
    assert isinstance(text, str), "text required"
    return text[:_MAX_CHARS]
