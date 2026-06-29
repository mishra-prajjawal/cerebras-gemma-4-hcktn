"""Meme Forge orchestration: fan out comedians -> fan in to the judge.
Bounded concurrency, bounded candidate set, fully audited."""
from __future__ import annotations
import asyncio
import time
from .cerebras_client import CerebrasClient
from .config import get_settings
from .contracts import CaptionSet, ImageIn, JudgeInput, Meme
from .personas import DEFAULT_PERSONAS
from .agents.comedian import Comedian
from .agents.judge import Judge

from typing import Sequence

_MAX_CANDIDATES = 60  # hard upper bound on captions handed to the judge


async def forge(image: ImageIn, personas: tuple[str, ...] = DEFAULT_PERSONAS) -> Meme:
    """Run the whole writers' room on one image. Precondition: at least one persona.
    Postcondition: a Meme with top_k captions and real timing."""
    assert isinstance(image, ImageIn), "forge needs an ImageIn"
    assert personas, "need at least one persona"
    client = CerebrasClient()
    s = get_settings()
    t0 = time.perf_counter()

    writers = [Comedian(client, p) for p in personas]
    results = await asyncio.gather(*(w.run(image) for w in writers),
                                   return_exceptions=True)
    candidates = _collect(results)
    assert candidates, "every comedian failed; cannot judge"

    ranking = await Judge(client).run(
        JudgeInput(topic=image.topic or "general internet humor", candidates=candidates))
    total_ms = round((time.perf_counter() - t0) * 1000, 2)
    return Meme(topic=image.topic, top=ranking.ranked[: s.top_k], writers=len(writers),
                total_ms=total_ms, tokens_per_sec=round(client.last_tokens_per_sec, 1))


def _collect(results: Sequence[object]) -> list[str]:
    """Flatten successful CaptionSets into a bounded candidate list."""
    out: list[str] = []
    for r in results:
        if isinstance(r, CaptionSet):
            out.extend(r.captions)
        if len(out) >= _MAX_CANDIDATES:
            return out[:_MAX_CANDIDATES]
    return out

