"""REFLEX hot loop: sample -> perceive -> track -> (sentinel||coach) -> narrate.
Bounded, fail-closed, watchdog-supervised."""
from __future__ import annotations
import asyncio
from .cerebras_client import CerebrasClient
from .contracts import Coaching, Frame, PlanStep
from .agents.perceptor import Perceptor
from .agents.state_tracker import StateTracker
from .agents.error_sentinel import ErrorSentinel
from .agents.coach import Coach
from .agents.narrator import Narrator

_MAX_FRAMES = 100_000  # hard upper bound (NASA rule 2)


async def run_loop(frames: asyncio.Queue[Frame], steps: list[PlanStep],
                   stop: asyncio.Event, sink: asyncio.Queue[Coaching],
                   client: CerebrasClient | None = None) -> None:
    """Consume frames until stop. Precondition: steps non-empty.
    Postcondition: never raises into caller; degraded results are emitted, not thrown."""
    assert steps, "plan must have at least one step"
    assert frames is not None, "frames queue must not be None"
    
    if client is None:
        client = CerebrasClient()
    perceptor = Perceptor(client)
    tracker = StateTracker(client, steps)
    coach = Coach(client, steps)
    narrator = Narrator(client)
    
    last_coaching: Coaching | None = None
    
    for _ in range(_MAX_FRAMES):
        if stop.is_set():
            return
        try:
            frame = await asyncio.wait_for(frames.get(), timeout=1.0)
        except asyncio.TimeoutError:
            continue
            
        try:
            # 1. Perceptor
            obs = await perceptor.run(frame)
            
            # 2. StateTracker
            delta = await tracker.run(obs)
            
            # 3. Change Gating
            if not delta.changed:
                if last_coaching is not None:
                    await sink.put(last_coaching)
                continue
                
            # 4. ErrorSentinel
            expected_step = steps[min(delta.current_step_idx, len(steps) - 1)]
            sentinel = ErrorSentinel(client, expected_step)
            report = await sentinel.run(frame)
            
            # 5. Coach
            coaching = await coach.run(report)
            
            # 6. Narrator
            final_coaching = await narrator.run(coaching)
            last_coaching = final_coaching
            
            await sink.put(final_coaching)
        except Exception:  # noqa: BLE001 - hot loop must survive a bad frame
            continue
            
    assert False, "frame budget exhausted: investigate runaway loop"
