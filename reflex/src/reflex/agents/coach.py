"""Coach agent (stub). TODO(agent): implement per CLAUDE.md + skills."""
from __future__ import annotations
from ..audit import audited
from ..contracts import ErrorReport, Coaching
from .base import Agent


from ..cerebras_client import CerebrasClient
from ..contracts import PlanStep

_SYS = ("You are an expert assembly coach. Convert an ErrorReport (verdict on the user's progress) "
        "into clear, direct spoken instruction ('say') and the step index they should focus on. "
        "If there are no errors, instruct them on what to do for the current step. "
        "Keep the instruction short, friendly, and actionable.")


class Coach(Agent[ErrorReport, Coaching]):
    name = "coach"

    def __init__(self, client: CerebrasClient, steps: list[PlanStep]) -> None:
        super().__init__(client)
        assert steps, "steps must not be empty"
        assert isinstance(steps, list), "steps must be a list"
        self._steps = steps
        self._current_step_idx = 0

    @audited("coach")
    async def run(self, data: ErrorReport) -> Coaching:
        """Precondition: data is an ErrorReport. Postcondition: a validated Coaching."""
        assert isinstance(data, ErrorReport), "input must be an ErrorReport"
        assert self._current_step_idx >= 0, "current step index must be non-negative"
        
        step_str = "\n".join(f"- Step {s.idx}: {s.title} (Expects: {s.expectation})" for s in self._steps)
        messages: list[dict[str, object]] = [
            {"role": "system", "content": _SYS},
            {"role": "user", "content": (
                f"PLAN STEPS:\n"
                f"{step_str}\n\n"
                f"ERROR REPORT:\n"
                f"Status: {data.status}\n"
                f"Deviation: {data.deviation}\n"
                f"Severity: {data.severity}\n"
                f"Fix Hint: {data.fix_hint}\n\n"
                f"User is currently on step: {self._current_step_idx}"
            )}
        ]
        
        coaching = await self._client.structured(
            messages=messages, out=Coaching, max_tokens=256)
            
        if data.status == "ok":
            self._current_step_idx = min(self._current_step_idx + 1, len(self._steps) - 1)
            
        assert isinstance(coaching, Coaching), "result must be a Coaching"
        return coaching
