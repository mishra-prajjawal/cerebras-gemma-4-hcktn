"""Moderator agent: reconciles all reviewer reports into one fail-closed verdict."""
from __future__ import annotations
from ..audit import audited
from ..config import get_settings
from ..contracts import ModeratorInput, Verdict
from .base import Agent

_SYS = ("You are the committee chair. Given each reviewer's cited findings, produce a "
        "single verdict. Fail closed: if any severity>=4 finding exists, overall_risk is "
        "at least 'high'. List the blocking issues plainly.")


class Moderator(Agent[ModeratorInput, Verdict]):
    name = "moderator"

    @audited("moderator")
    async def run(self, data: ModeratorInput) -> Verdict:
        """Precondition: at least one report. Postcondition: validated Verdict."""
        assert isinstance(data, ModeratorInput), "moderator input must be ModeratorInput"
        assert data.reports, "no reports to synthesize"
        s = get_settings()
        lines: list[str] = []
        for rep in data.reports:
            for f in rep.findings:
                lines.append("[" + rep.reviewer + " sev" + str(f.severity) + "] "
                             + f.issue + " || cite: " + f.citation)
        body = chr(10).join(lines) if lines else "No cited findings reported."
        messages: list[dict[str, object]] = [
            {"role": "system", "content": _SYS},
            {"role": "user", "content": "FINDINGS:" + chr(10) + body},
        ]
        verdict = await self._client.structured(
            messages=messages, out=Verdict, max_tokens=s.moderator_max_tokens)

        # Enforce fail-closed in code: if any severity >= 4 finding exists, overall_risk is at least 'high'
        has_high_severity = any(
            f.severity >= 4
            for rep in data.reports
            for f in rep.findings
        )
        if has_high_severity and verdict.overall_risk not in ("high", "critical"):
            verdict = verdict.model_copy(update={"overall_risk": "high"})

        assert isinstance(verdict, Verdict), "output must be Verdict"
        return verdict
