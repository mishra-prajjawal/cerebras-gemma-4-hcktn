import os
import pytest
from unittest.mock import AsyncMock, MagicMock

# Setup mock key before importing client/config
os.environ["CEREBRAS_API_KEY"] = "csk-mockkey123456"

from reflex.cerebras_client import CerebrasClient
from reflex.contracts import Frame, PlanStep, Observation, StateDelta, ErrorReport, Coaching
from reflex.agents.perceptor import Perceptor
from reflex.agents.state_tracker import StateTracker
from reflex.agents.error_sentinel import ErrorSentinel
from reflex.agents.coach import Coach
from reflex.agents.narrator import Narrator


@pytest.mark.asyncio
async def test_perceptor() -> None:
    client = MagicMock(spec=CerebrasClient)
    obs_mock = Observation(objects=["screw", "screwdriver"], summary="Workbench is set up.", confidence=0.95)
    client.structured = AsyncMock(return_value=obs_mock)
    
    perceptor = Perceptor(client)
    frame = Frame(ts=123.45, seq=0, jpeg_b64="YmVlcGJvb3A=")  # base64 encoded 'beepboop'
    
    res = await perceptor.run(frame)
    assert isinstance(res, Observation)
    assert res.objects == ["screw", "screwdriver"]
    assert res.confidence == 0.95
    client.structured.assert_called_once()


@pytest.mark.asyncio
async def test_state_tracker() -> None:
    client = MagicMock(spec=CerebrasClient)
    delta_mock = StateDelta(changed=True, current_step_idx=1, notes="Progress made.")
    client.structured = AsyncMock(return_value=delta_mock)
    
    steps = [
        PlanStep(idx=0, title="Prep", expectation="Clean workspace"),
        PlanStep(idx=1, title="Assembly", expectation="First screw inserted")
    ]
    tracker = StateTracker(client, steps)
    
    # First call sets initial state (changed=True, index=0) without model call
    obs1 = Observation(objects=[], summary="Empty bench", confidence=1.0)
    res1 = await tracker.run(obs1)
    assert res1.changed is True
    assert res1.current_step_idx == 0
    client.structured.assert_not_called()
    
    # Second call should invoke model comparing obs1 and obs2
    obs2 = Observation(objects=["screw"], summary="Screw added", confidence=0.9)
    res2 = await tracker.run(obs2)
    assert res2.changed is True
    assert res2.current_step_idx == 1
    client.structured.assert_called_once()


@pytest.mark.asyncio
async def test_error_sentinel() -> None:
    client = MagicMock(spec=CerebrasClient)
    report_mock = ErrorReport(status="ok", deviation="none", severity=0, fix_hint="good job")
    client.structured = AsyncMock(return_value=report_mock)
    
    step = PlanStep(idx=0, title="Prep", expectation="Clean workspace")
    sentinel = ErrorSentinel(client, step)
    frame = Frame(ts=123.45, seq=0, jpeg_b64="YmVlcGJvb3A=")
    
    res = await sentinel.run(frame)
    assert isinstance(res, ErrorReport)
    assert res.status == "ok"
    assert res.severity == 0
    client.structured.assert_called_once()


@pytest.mark.asyncio
async def test_coach() -> None:
    client = MagicMock(spec=CerebrasClient)
    coaching_mock = Coaching(say="Insert the screw", show_step_idx=1)
    client.structured = AsyncMock(return_value=coaching_mock)
    
    steps = [
        PlanStep(idx=0, title="Prep", expectation="Clean workspace"),
        PlanStep(idx=1, title="Assembly", expectation="First screw inserted")
    ]
    coach = Coach(client, steps)
    report = ErrorReport(status="ok", deviation="none", severity=0, fix_hint="continue")
    
    res = await coach.run(report)
    assert isinstance(res, Coaching)
    assert res.say == "Insert the screw"
    assert res.show_step_idx == 1
    client.structured.assert_called_once()


@pytest.mark.asyncio
async def test_narrator() -> None:
    client = MagicMock(spec=CerebrasClient)
    coaching_mock = Coaching(say="Polished: Insert the screw", show_step_idx=1)
    client.structured = AsyncMock(return_value=coaching_mock)
    
    narrator = Narrator(client)
    input_coaching = Coaching(say="Insert the screw", show_step_idx=1)
    
    res = await narrator.run(input_coaching)
    assert isinstance(res, Coaching)
    assert res.say == "Polished: Insert the screw"
    assert res.show_step_idx == 1
    client.structured.assert_called_once()
