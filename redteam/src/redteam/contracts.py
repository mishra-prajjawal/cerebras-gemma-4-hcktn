"""Typed I/O boundaries for the Red-Team Committee."""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class Strict(BaseModel):
    """Base for model-facing schemas: forbids extra keys (Cerebras strict mode)."""
    model_config = ConfigDict(extra="forbid")


class DocIn(BaseModel):
    """Document under review: text and/or a screenshot (base64 jpeg)."""
    text: str = ""
    jpeg_b64: str = ""


class Finding(Strict):
    """One cited issue. citation MUST be a verbatim quote from the document."""
    clause: str
    issue: str
    severity: int = Field(ge=0, le=5)
    citation: str
    recommendation: str
    char_start: int = -1
    char_end: int = -1


class VisionOutput(Strict):
    """Output of the vision reader model call."""
    extracted_text: str


class ReviewerInput(BaseModel):
    """A single reviewer role plus the document text it must attack."""
    role: str
    doc_text: str = Field(min_length=1)


class ReviewerReport(Strict):
    """One reviewer's cited findings (may be empty if nothing material found)."""
    reviewer: str
    findings: list[Finding]


class ModeratorInput(BaseModel):
    """All reviewer reports, handed to the moderator for synthesis."""
    reports: list[ReviewerReport] = Field(min_length=1)


class Verdict(Strict):
    """Moderator output: the fail-closed committee decision."""
    overall_risk: Literal["low", "medium", "high", "critical"]
    summary: str
    blocking_issues: list[str]
