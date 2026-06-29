"""Reviewer agent: one role, attacks the document, returns cited findings only."""
from __future__ import annotations
from ..audit import audited
from ..config import get_settings
from ..contracts import ReviewerInput, ReviewerReport
from .base import Agent


class Reviewer(Agent[ReviewerInput, ReviewerReport]):
    name = "reviewer"

    @audited("reviewer")
    async def run(self, data: ReviewerInput) -> ReviewerReport:
        """Precondition: ReviewerInput with text. Postcondition: cited ReviewerReport.
        Grounding rule: every finding.citation must be a verbatim quote from the doc."""
        assert isinstance(data, ReviewerInput), "reviewer input must be ReviewerInput"
        assert data.doc_text, "no document text to review"
        s = get_settings()
        system = (
            "You are " + data.role + " Review ONLY the document text provided. For each "
            "issue, the citation field MUST be a verbatim quote copied from the document; "
            "if you cannot quote it, do not report it. Be specific and terse."
        )
        messages: list[dict[str, object]] = [
            {"role": "system", "content": system},
            {"role": "user", "content": "DOCUMENT:" + chr(10) + data.doc_text},
        ]
        out = await self._client.structured(
            messages=messages, out=ReviewerReport, max_tokens=s.reviewer_max_tokens)
        return _grounded(out, data.doc_text)


def _grounded(report: ReviewerReport, doc: str) -> ReviewerReport:
    """Drop findings whose citation is not actually in the document (fail-closed)
    and calculate exact character offsets in doc."""
    assert isinstance(report, ReviewerReport), "report must be ReviewerReport"
    assert isinstance(doc, str), "doc must be str"
    kept = []
    for f in report.findings:
        if f.citation and f.citation in doc:
            start = doc.find(f.citation)
            end = start + len(f.citation)
            f.char_start = start
            f.char_end = end
            kept.append(f)
    res = ReviewerReport(reviewer=report.reviewer, findings=kept)
    assert isinstance(res, ReviewerReport), "output must be ReviewerReport"
    return res
