import asyncio
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Set mock API key before importing client/config
os.environ["CEREBRAS_API_KEY"] = "csk-mockkey123456"

from reflex.contracts import Frame, PlanStep, Observation, StateDelta, ErrorReport, Coaching
from reflex.cerebras_client import CerebrasClient
from reflex.orchestrator import run_loop


@pytest.mark.asyncio
async def test_orchestrator_run_loop() -> None:
    # 1. Create mock plan steps
    steps = [
        PlanStep(idx=0, title="Step 0", expectation="Initial expectation"),
        PlanStep(idx=1, title="Step 1", expectation="Next expectation")
    ]
    
    # 2. Setup mock frame queues
    frames_queue: asyncio.Queue[Frame] = asyncio.Queue()
    sink_queue: asyncio.Queue[Coaching] = asyncio.Queue()
    stop_event = asyncio.Event()
    
    # Put two frames in
    await frames_queue.put(Frame(ts=1.0, seq=0, jpeg_b64="YmVlcGJvb3A="))
    await frames_queue.put(Frame(ts=2.0, seq=1, jpeg_b64="YmVlcGJvb3A="))
    
    obs = Observation(objects=["widget"], summary="bench contains widget", confidence=0.9)
    coaching_out_1 = Coaching(say="Step 0 Complete!", show_step_idx=0)
    coaching_out_2 = Coaching(say="Polished: Step 0 Complete!", show_step_idx=0)
    
    # Mock CerebrasClient.structured directly
    with patch.object(CerebrasClient, "structured", new_callable=AsyncMock) as mock_structured:
        mock_structured.side_effect = [
            obs,  # Perceptor frame 0
            ErrorReport(status="ok", deviation="none", severity=0, fix_hint="great"),  # Sentinel frame 0
            coaching_out_1,  # Coach frame 0
            coaching_out_2,  # Narrator frame 0
            
            obs,  # Perceptor frame 1
            StateDelta(changed=False, current_step_idx=0, notes="No change"),  # Tracker frame 1 (gets called because it compares obs to previous obs)
        ]
        
        # Start orchestrator in a background task
        loop_task = asyncio.create_task(run_loop(frames_queue, steps, stop_event, sink_queue))
        
        # Wait a little for processing
        await asyncio.sleep(0.5)
        stop_event.set()
        
        # Wait for loop_task to exit
        try:
            await asyncio.wait_for(loop_task, timeout=1.0)
        except asyncio.TimeoutError:
            loop_task.cancel()
            
        # We expect two items in the sink:
        # Item 1: polished coaching from frame 0
        # Item 2: repeat of last coaching due to changed=False in frame 1
        assert sink_queue.qsize() == 2
        
        item1 = sink_queue.get_nowait()
        assert item1.say == "Polished: Step 0 Complete!"
        
        item2 = sink_queue.get_nowait()
        assert item2.say == "Polished: Step 0 Complete!"
