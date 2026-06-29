import asyncio
import pytest
from reflex.telemetry import Telemetry
from reflex.gemini_baseline import gemini_sentinel
from reflex.contracts import Frame


def test_telemetry_observe_and_stats() -> None:
    tel = Telemetry(window_size=3)
    
    # Verify initial stats
    stats = tel.get_stats()
    assert stats["avg_tps"] == 0.0
    assert stats["p50_latency_ms"] == 0.0
    
    # Add observations
    tel.observe(100.0, 50.0)
    tel.observe(200.0, 150.0)
    tel.observe(150.0, 100.0)
    
    stats = tel.get_stats()
    assert stats["avg_tps"] == 150.0  # (100+200+150)/3 = 150
    assert stats["p50_latency_ms"] == 100.0  # Median of [50, 100, 150] is 100
    
    # Observe one more, check rolling eviction (window_size=3)
    tel.observe(300.0, 20.0)
    # Window should now contain: [200, 150, 300] and lats [150, 100, 20]
    stats = tel.get_stats()
    assert stats["avg_tps"] == 216.66666666666666  # (200+150+300)/3
    assert stats["p50_latency_ms"] == 100.0  # Median of [20, 100, 150] is 100


@pytest.mark.asyncio
async def test_gemini_baseline() -> None:
    frame = Frame(ts=1.0, seq=0, jpeg_b64="YmVlcGJvb3A=")
    report, latency = await gemini_sentinel(frame, "Clean workbench")
    
    assert report.status == "ok"
    assert latency >= 1800.0  # Simulated sleep is 1.8s
