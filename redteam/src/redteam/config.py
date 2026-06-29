"""Frozen settings for the Red-Team Committee."""
from __future__ import annotations
import functools
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
load_dotenv()


class Settings(BaseModel, frozen=True):
    cerebras_api_key: str = Field(min_length=1)
    base_url: str = "https://api.cerebras.ai/v1"
    model_id: str = "gemma-4-31b"
    max_rpm: int = 100
    max_tpm: int = 100_000
    max_concurrency: int = 6
    reviewer_max_tokens: int = 640
    moderator_max_tokens: int = 512
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
