"""Frozen settings for REFLEX (OpenAI-compatible Cerebras endpoint)."""
from __future__ import annotations
import functools
import os
from pydantic import BaseModel, Field


class Settings(BaseModel, frozen=True):
    cerebras_api_key: str = Field(min_length=1)
    base_url: str = "https://api.cerebras.ai/v1"
    model_id: str = "gemma-4-31b"
    max_rpm: int = 100
    max_tpm: int = 100_000
    max_concurrency: int = 4
    target_fps: float = 2.0          # frames sampled per second
    sentinel_max_tokens: int = 384
    jpeg_max_edge: int = 768


@functools.lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Read env once. Only CEREBRAS_API_KEY is required; rest have defaults."""
    key = os.environ.get("CEREBRAS_API_KEY", "")
    assert key, "CEREBRAS_API_KEY is required"
    settings = Settings(
        cerebras_api_key=key,
        base_url=os.environ.get("CEREBRAS_BASE_URL", "https://api.cerebras.ai/v1"),
        model_id=os.environ.get("MODEL_ID", "gemma-4-31b"),
    )
    assert settings.model_id == "gemma-4-31b", "only model id gemma-4-31b is supported"
    return settings
