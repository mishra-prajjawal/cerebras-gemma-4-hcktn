"""StateTracker agent (stub). TODO(agent): implement per CLAUDE.md + skills."""
from __future__ import annotations
from ..audit import audited
from ..contracts import Observation, StateDelta
from .base import Agent


from ..cerebras_client import CerebrasClient
from ..contracts import PlanStep

_SYS = ("You are an assembly state tracking agent. Compare the current observation of the workbench "
        "to the previous observation. Determine if a meaningful physical change has occurred (e.g. "
        "a new part placed, a tool moved, assembly progress made) vs just minor noise. "
        "Output whether it changed, the current step index, and notes on the delta.")


class StateTracker(Agent[Observation, StateDelta]):
    name = "state_tracker"

    def __init__(self, client: CerebrasClient, steps: list[PlanStep]) -> None:
        super().__init__(client)
        assert steps, "steps cannot be empty"
        assert isinstance(steps, list), "steps must be a list"
        self._steps = steps
        self._last_obs: Observation | None = None
        self._current_step_idx = 0

    @audited("state_tracker")
    async def run(self, data: Observation) -> StateDelta:
        """Precondition: data is an Observation. Postcondition: a validated StateDelta."""
        assert isinstance(data, Observation), "input must be an Observation"
        assert self._current_step_idx >= 0, "current step index must be non-negative"
        
        if self._last_obs is None:
            self._last_obs = data
            res = StateDelta(changed=True, current_step_idx=self._current_step_idx, notes="Initial state established.")
            assert isinstance(res, StateDelta), "result must be a StateDelta"
            return res
            
        step_str = "\n".join(f"- Step {s.idx}: {s.title} (Expects: {s.expectation})" for s in self._steps)
        messages: list[dict[str, object]] = [
            {"role": "system", "content": _SYS},
            {"role": "user", "content": (
                f"PLAN STEPS:\n"
                f"{step_str}\n\n"
                f"PREVIOUS OBSERVATION:\n"
                f"Objects: {self._last_obs.objects}\n"
                f"Summary: {self._last_obs.summary}\n\n"
                f"CURRENT OBSERVATION:\n"
                f"Objects: {data.objects}\n"
                f"Summary: {data.summary}\n\n"
                f"Current expected step: {self._current_step_idx}"
            )}
        ]
        
        delta = await self._client.structured(
            messages=messages, out=StateDelta, max_tokens=256)
        
        self._last_obs = data
        self._current_step_idx = delta.current_step_idx
        
        assert isinstance(delta, StateDelta), "result must be a StateDelta"
        return delta
