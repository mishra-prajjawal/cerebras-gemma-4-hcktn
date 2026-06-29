"""Judge agent: scores and ranks every candidate caption in one call."""
from __future__ import annotations
from ..audit import audited
from ..config import get_settings
from ..contracts import JudgeInput, Ranking
from .base import Agent

_SYS = ("You are a viral-meme editor. Score each caption 0-100 for how likely it is to "
        "make someone screenshot and share it. Rank best first. Keep reasons to a phrase.")


class Judge(Agent[JudgeInput, Ranking]):
    name = "judge"

    @audited("judge")
    async def run(self, data: JudgeInput) -> Ranking:
        """Precondition: non-empty candidates. Postcondition: validated Ranking."""
        assert isinstance(data, JudgeInput), "judge input must be JudgeInput"
        assert data.candidates, "nothing to rank"
        s = get_settings()
        listing = chr(10).join(str(i) + ". " + c for i, c in enumerate(data.candidates))
        user = "TOPIC: " + data.topic + chr(10) + "CAPTIONS:" + chr(10) + listing
        messages: list[dict[str, object]] = [
            {"role": "system", "content": _SYS},
            {"role": "user", "content": user},
        ]
        out = await self._client.structured(
            messages=messages, out=Ranking, max_tokens=s.judge_max_tokens)
        assert out.ranked, "judge returned no ranking"
        return out
