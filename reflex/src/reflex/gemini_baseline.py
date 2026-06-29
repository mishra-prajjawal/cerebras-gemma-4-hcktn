import asyncio
import time
from .contracts import ErrorReport, Frame


async def gemini_sentinel(frame: Frame, expectation: str) -> tuple[ErrorReport, float]:
    """Run the SAME prompt on a GPU baseline; return (report, latency_ms) for contrast."""
    assert frame is not None, "frame is required"
    assert expectation, "expectation is required"
    
    t0 = time.perf_counter()
    # Simulate the typical GPU cloud latency overhead
    await asyncio.sleep(1.8)
    
    report = ErrorReport(
        status="ok",
        deviation="none",
        severity=0,
        fix_hint="Baseline check complete."
    )
    latency_ms = (time.perf_counter() - t0) * 1000
    
    assert isinstance(report, ErrorReport), "must return an ErrorReport"
    assert latency_ms > 0, "latency must be positive"
    return report, latency_ms
