"""Typed I/O boundaries for Meme Forge. Every agent edge is one of these."""
from __future__ import annotations
from pydantic import BaseModel, ConfigDict, Field


class Strict(BaseModel):
    """Base for model-facing schemas: forbids extra keys (Cerebras strict mode)."""
    model_config = ConfigDict(extra="forbid")


class ImageIn(BaseModel):
    """Input image to caption (base64 jpeg) plus an optional steer topic."""
    jpeg_b64: str = Field(min_length=1)
    topic: str = ""


class CaptionSet(Strict):
    """One comedian's output: a persona voice + its captions."""
    persona: str
    captions: list[str] = Field(min_length=1, max_length=5)


class JudgeInput(BaseModel):
    """All candidate captions, flattened, handed to the judge."""
    topic: str
    candidates: list[str] = Field(min_length=1)


class RankedCaption(Strict):
    """One scored caption from the judge."""
    text: str
    score: int = Field(ge=0, le=100)
    reason: str


class Ranking(Strict):
    """Judge output: every candidate scored + ranked, best first."""
    ranked: list[RankedCaption] = Field(min_length=1)


class Meme(BaseModel):
    """Final pipeline result for the UI: top captions + timing flex."""
    topic: str
    top: list[RankedCaption]
    writers: int
    total_ms: float
    tokens_per_sec: float
