"""ErrorSentinel: compares the live frame to the expected step; flags deviations."""
from __future__ import annotations
from ..audit import audited
from ..contracts import ErrorReport, Frame, PlanStep
from .base import Agent

from ..cerebras_client import CerebrasClient

_SYS = ("You are an assembly QA inspector. Compare the image to the EXPECTED step. "
        "Report only real, visible deviations. Be terse and specific.")


class ErrorSentinel(Agent[Frame, ErrorReport]):
    name = "error_sentinel"

    def __init__(self, client: CerebrasClient, step: PlanStep) -> None:
        super().__init__(client)
        assert step is not None, "sentinel needs the current plan step"
        assert isinstance(step, PlanStep), "step must be a PlanStep"
        self._step = step

    @audited("error_sentinel")
    async def run(self, data: Frame) -> ErrorReport:
        """Precondition: data is a Frame. Postcondition: a validated ErrorReport."""
        assert isinstance(data, Frame), "sentinel input must be a Frame"
        url = f"data:image/jpeg;base64,{data.jpeg_b64}"
        messages: list[dict[str, object]] = [
            {"role": "system", "content": _SYS},
            {"role": "user", "content": [
                {"type": "text", "text": f"EXPECTED: {self._step.expectation}"},
                {"type": "image_url", "image_url": {"url": url}},
            ]},
        ]
        report = await self._client.structured(
            messages=messages, out=ErrorReport, max_tokens=384)
        assert 0 <= report.severity <= 5, "severity out of range"
        return report
