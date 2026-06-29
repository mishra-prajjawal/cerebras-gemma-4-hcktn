"""Typed I/O boundaries for REFLEX. Every agent edge is one of these."""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class Strict(BaseModel):
    """Base for all model-facing schemas: forbids extra keys (Cerebras strict)."""
    model_config = ConfigDict(extra="forbid")


class Frame(BaseModel):
    """A sampled webcam frame."""
    ts: float
    seq: int = Field(ge=0)
    jpeg_b64: str = Field(min_length=1)


class PlanStep(Strict):
    idx: int = Field(ge=0)
    title: str
    expectation: str            # what the bench should look like when correct


class Observation(Strict):
    """Perceptor output: what is visibly on the bench right now."""
    objects: list[str]
    summary: str
    confidence: float = Field(ge=0, le=1)


class StateDelta(Strict):
    """StateTracker output: change vs last observation."""
    changed: bool
    current_step_idx: int = Field(ge=0)
    notes: str


class ErrorReport(Strict):
    """ErrorSentinel output: the safety-critical verdict."""
    status: Literal["ok", "warn", "error"]
    deviation: str
    severity: int = Field(ge=0, le=5)
    fix_hint: str


class Coaching(Strict):
    """Coach output: the next instruction for the human."""
    say: str
    show_step_idx: int = Field(ge=0)
