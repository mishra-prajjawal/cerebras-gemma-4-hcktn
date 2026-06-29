import asyncio
import os
import pytest
from PIL import Image

# Setup mock key before importing anything else
os.environ["CEREBRAS_API_KEY"] = "csk-mockkey123456"

from reflex.frames import capture, process_frame
from reflex.contracts import Frame


def test_process_frame() -> None:
    # Test image resizing and JPEG/base64 encoding
    img = Image.new("RGB", (1000, 500), color="blue")
    frame = process_frame(img, seq=5)
    
    assert isinstance(frame, Frame)
    assert frame.seq == 5
    assert len(frame.jpeg_b64) > 0
    
    # Check that it resized. Since max_edge is 768, the 1000 edge should downscale to 768.
    # We can decode and open it to verify dimensions.
    import base64
    import io
    decoded = base64.b64decode(frame.jpeg_b64)
    img_out = Image.open(io.BytesIO(decoded))
    assert img_out.size[0] == 768
    assert img_out.size[1] == 384


@pytest.mark.asyncio
async def test_capture_loop() -> None:
    # Test that capture loop runs, enqueues frames, and stops when event is set
    queue: asyncio.Queue[Frame] = asyncio.Queue(maxsize=5)
    stop_event = asyncio.Event()
    
    # Start capture task
    task = asyncio.create_task(capture(queue, fps=10.0, stop=stop_event))
    
    # Wait for a couple of frames
    await asyncio.sleep(0.3)
    stop_event.set()
    await task
    
    assert queue.qsize() > 0
    frame = queue.get_nowait()
    assert isinstance(frame, Frame)
    assert frame.seq == 0
