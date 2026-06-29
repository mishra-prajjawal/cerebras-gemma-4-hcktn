"""Integration tests for the Red-Team Committee pipeline."""
from __future__ import annotations
import pytest
from redteam.contracts import DocIn
from redteam.pipeline import review


@pytest.mark.asyncio
async def test_pipeline_eval() -> None:
    """Evaluate known-bad contract and assert committee catches the issues with perfect grounding."""
    text = (
        "SERVICES AGREEMENT\n\n"
        "1. Term: The initial term is one year. An auto-renewal fee of 50% will be added annually.\n"
        "2. Limitation of Liability: Under no circumstances shall the liability of Vendor exceed $0.\n"
        "3. SLA: Vendor may suspend service at any time without notice or SLA penalty.\n"
        "4. Data: Customer data will be stored on public, unencrypted servers, and breaches will not be reported.\n"
    )
    doc = DocIn(text=text)

    # Run review
    verdict, ms, text_out, reports, tokens_sec = await review(doc)

    # 1. Assertions on the verdict (fail-closed)
    assert verdict.overall_risk in ("high", "critical"), "moderator must return high/critical risk for bad contract"
    assert len(verdict.blocking_issues) > 0, "blocking issues must be found"
    assert len(verdict.summary) > 0, "summary must be present"

    # 2. Assertions on findings and grounding/citations
    assert len(reports) > 0, "reviewer reports must be populated"

    found_any_finding = False
    for rep in reports:
        assert rep.reviewer, "reviewer name must be populated"
        for f in rep.findings:
            found_any_finding = True
            # Verbatim citation grounding test
            assert f.citation, "citation must be non-empty"
            assert f.citation in text, f"citation '{f.citation}' not found in source text"
            assert f.char_start != -1, "char_start offset must be computed"
            assert f.char_end != -1, "char_end offset must be computed"
            assert text[f.char_start:f.char_end] == f.citation, "char offsets must match the verbatim quote exactly"

    assert found_any_finding, "committee failed to find any issues in a known-bad contract!"
