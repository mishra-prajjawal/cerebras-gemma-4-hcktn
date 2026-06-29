"""Red-Team Committee orchestration: fan out reviewers -> moderator verdict.
Bounded, parallel, fully audited, fail-closed."""
from __future__ import annotations
import asyncio
import time
from .cerebras_client import CerebrasClient
from .contracts import DocIn, ModeratorInput, ReviewerInput, ReviewerReport, Verdict
from .ingest import clip
from .roles import ROLES
from .agents.reviewer import Reviewer
from .agents.moderator import Moderator


async def review(doc: DocIn) -> tuple[Verdict, float, str, list[ReviewerReport], float]:
    """Run the full committee on a document. Precondition: doc has text or image.
    Postcondition: (validated Verdict, wall_ms, text, reports, tokens_per_sec). Never raises into the caller for a
    single reviewer failure; only an all-fail or moderator failure propagates."""
    assert isinstance(doc, DocIn), "review needs a DocIn"
    assert doc.text or doc.jpeg_b64, "review needs either text or image"
    client = CerebrasClient()
    t0 = time.perf_counter()

    if doc.jpeg_b64 and not doc.text:
        from .agents.vision_reader import VisionReader
        vision_res = await VisionReader(client).run(doc)
        text = clip(vision_res.doc_text)
    else:
        text = clip(doc.text)

    reviewer = Reviewer(client)
    inputs = [ReviewerInput(role=name + " - " + brief, doc_text=text)
              for name, brief in ROLES.items()]
    raw = await asyncio.gather(*(reviewer.run(i) for i in inputs),
                               return_exceptions=True)
    reports = [r for r in raw if isinstance(r, ReviewerReport)]
    assert reports, "every reviewer failed; cannot reach a verdict"

    verdict = await Moderator(client).run(ModeratorInput(reports=reports))
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    assert isinstance(verdict, Verdict), "output verdict must be a Verdict"
    return verdict, latency_ms, text, reports, client.last_tokens_per_sec
