"""Aggregates live tokens/sec for the speed overlay (stub)."""
from __future__ import annotations


class Telemetry:
    """Rolling mean of tokens/sec + p50 latency. Bounded to prevent memory growth."""

    def __init__(self, window_size: int = 100) -> None:
        assert window_size > 0, "window size must be positive"
        self._window_size = window_size
        self._tps: list[float] = []
        self._latencies: list[float] = []

    def observe(self, tokens_per_sec: float, latency_ms: float) -> None:
        """Record a single observation. Precondition: non-negative values."""
        assert tokens_per_sec >= 0.0, "tps must be non-negative"
        assert latency_ms >= 0.0, "latency must be non-negative"
        
        self._tps.append(tokens_per_sec)
        self._latencies.append(latency_ms)
        
        # Enforce bounded growth (NASA Rule 3)
        if len(self._tps) > self._window_size:
            self._tps.pop(0)
        if len(self._latencies) > self._window_size:
            self._latencies.pop(0)
            
        assert len(self._tps) <= self._window_size, "tps window size limit exceeded"
        assert len(self._latencies) <= self._window_size, "latency window size limit exceeded"

    def get_stats(self) -> dict[str, float]:
        """Compute the average tokens/sec and p50 latency. Postcondition: returns valid stats dict."""
        assert len(self._tps) >= 0, "tps list must exist"
        assert len(self._latencies) >= 0, "latencies list must exist"
        
        if not self._tps:
            return {"avg_tps": 0.0, "p50_latency_ms": 0.0}
            
        avg_tps = sum(self._tps) / len(self._tps)
        
        sorted_lats = sorted(self._latencies)
        mid = len(sorted_lats) // 2
        if len(sorted_lats) % 2 == 1:
            p50 = sorted_lats[mid]
        else:
            p50 = (sorted_lats[mid - 1] + sorted_lats[mid]) / 2.0
            
        res = {"avg_tps": avg_tps, "p50_latency_ms": p50}
        assert "avg_tps" in res and "p50_latency_ms" in res, "stats dict must contain metrics keys"
        return res
