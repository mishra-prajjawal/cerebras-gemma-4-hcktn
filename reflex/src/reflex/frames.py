import asyncio
import base64
import io
import time
from PIL import Image, ImageDraw
from .contracts import Frame
from .config import get_settings

try:
    import cv2  # type: ignore[import-not-found]
except ImportError:
    cv2 = None


def process_frame(img: Image.Image, seq: int) -> Frame:
    """Resize, compress to JPEG, encode to base64. Precondition: img is a PIL Image."""
    assert isinstance(img, Image.Image), "img must be a PIL Image"
    assert seq >= 0, "sequence number must be non-negative"
    
    settings = get_settings()
    w, h = img.size
    max_edge = settings.jpeg_max_edge
    
    if max(w, h) > max_edge:
        if w > h:
            img = img.resize((max_edge, int(h * max_edge / w)), Image.Resampling.LANCZOS)
        else:
            img = img.resize((int(w * max_edge / h), max_edge), Image.Resampling.LANCZOS)
            
    out_io = io.BytesIO()
    img.save(out_io, format="JPEG", quality=70)
    b64 = base64.b64encode(out_io.getvalue()).decode("utf-8")
    
    res = Frame(ts=time.time(), seq=seq, jpeg_b64=b64)
    assert len(res.jpeg_b64) > 0, "encoded frame base64 must be non-empty"
    return res


async def capture(out: asyncio.Queue[Frame], fps: float, stop: asyncio.Event) -> None:
    """Sample the webcam (or mock if no camera/cv2), enqueue Frames. Bounded by stop."""
    assert fps > 0.0, "fps must be positive"
    assert out is not None, "queue must not be None"
    
    interval = 1.0 / fps
    seq = 0
    cap = None
    
    if cv2 is not None:
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                cap = None
        except Exception:  # noqa: BLE001
            cap = None
            
    for _ in range(100_000):  # Bounded loop (NASA Rule 2)
        if stop.is_set():
            break
        t0 = time.perf_counter()
        
        img = None
        if cap is not None and cv2 is not None:
            ret, frame = cap.read()
            if ret and frame is not None:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(rgb)
                
        if img is None:
            img = Image.new("RGB", (640, 480), color=(128, 128, 128))
            draw = ImageDraw.Draw(img)
            draw.text((50, 200), f"REFLEX MOCK CAMERA - SEQ {seq}", fill=(255, 255, 255))
            
        frame_obj = process_frame(img, seq)
        seq += 1
        
        try:
            out.put_nowait(frame_obj)
        except asyncio.QueueFull:
            pass  # Drop frame to avoid latency build-up
            
        elapsed = time.perf_counter() - t0
        delay = max(0.0, interval - elapsed)
        await asyncio.sleep(delay)
        
    if cap is not None:
        cap.release()
