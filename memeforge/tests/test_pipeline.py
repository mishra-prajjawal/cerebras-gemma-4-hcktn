from __future__ import annotations
import pytest
from unittest.mock import patch, AsyncMock
from memeforge.contracts import ImageIn, CaptionSet, Ranking, RankedCaption
from memeforge.pipeline import forge


@pytest.mark.anyio
async def test_forge_pipeline_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CEREBRAS_API_KEY", "mocked-key-for-testing")
    
    async def mock_structured(messages: list[dict[str, object]], out: type, **kwargs: object) -> object:
        assert messages, "messages cannot be empty"
        assert out is not None, "out model cannot be None"
        if out == CaptionSet:
            sys_msg = messages[0]["content"]
            assert isinstance(sys_msg, str)
            persona = "unknown"
            if sys_msg.startswith("You are "):
                persona = sys_msg.split(",")[0].replace("You are ", "")
            return CaptionSet(persona=persona, captions=[f"Joke from {persona} 1", f"Joke from {persona} 2"])
        elif out == Ranking:
            user_msg = messages[1]["content"]
            assert isinstance(user_msg, str)
            lines = user_msg.split("\n")
            candidates = [line.split(". ", 1)[1] for line in lines if line and ". " in line]
            assert candidates, "candidates list empty in judge input"
            ranked = [
                RankedCaption(text=c, score=90 - i, reason="solid joke")
                for i, c in enumerate(candidates)
            ]

            return Ranking(ranked=ranked)
        raise ValueError(f"Unexpected output type: {out}")

    with patch("memeforge.cerebras_client.CerebrasClient.structured", new=AsyncMock(side_effect=mock_structured)):
        img = ImageIn(jpeg_b64="dGVzdA==", topic="testing")
        result = await forge(img, personas=("comedian a", "comedian b"))
        assert result.writers == 2, "mismatched writer count"
        assert len(result.top) > 0, "no ranked memes returned"
        assert result.topic == "testing", "steer topic was modified"
        assert result.top[0].score >= result.top[-1].score, "memes not ranked by score descending"
