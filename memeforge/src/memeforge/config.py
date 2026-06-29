"""Frozen settings for Meme Forge."""
from __future__ import annotations
import functools
import os
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseModel, frozen=True):
    cerebras_api_key: str = Field(min_length=1)
    base_url: str = "https://api.cerebras.ai/v1"
    model_id: str = "gemma-4-31b"
    max_rpm: int = 100
    max_tpm: int = 100_000
    max_concurrency: int = 8      # the writers' room runs wide
    caption_max_tokens: int = 256
    judge_max_tokens: int = 2048
    top_k: int = 3                # memes returned to the user
    jpeg_max_edge: int = 768


@functools.lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Read env once. Only CEREBRAS_API_KEY is required."""
    key = os.environ.get("CEREBRAS_API_KEY", "")
    assert key, "CEREBRAS_API_KEY is required"
    return Settings(
        cerebras_api_key=key,
        base_url=os.environ.get("CEREBRAS_BASE_URL", "https://api.cerebras.ai/v1"),
        model_id=os.environ.get("MODEL_ID", "gemma-4-31b"))
