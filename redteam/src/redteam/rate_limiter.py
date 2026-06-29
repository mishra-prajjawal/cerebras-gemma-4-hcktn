"""Token-bucket rate limiter enforcing 100 RPM and 100K TPM. Fail-safe by waiting."""
from __future__ import annotations
import asyncio
import time


class RateLimiter:
    """Dual bucket: requests/min and tokens/min. All model calls MUST acquire()."""

    def __init__(self, max_rpm: int, max_tpm: int) -> None:
        assert max_rpm > 0 and max_tpm > 0, "budgets must be positive"
        self._rpm = max_rpm
        self._tpm = max_tpm
        self._req_times: list[float] = []
        self._tok_events: list[tuple[float, int]] = []
        self._lock = asyncio.Lock()

    async def acquire(self, est_tokens: int) -> None:
        """Block until a call of est_tokens fits both budgets. Bounded wait per attempt."""
        assert est_tokens >= 0, "token estimate must be non-negative"
        for _ in range(1000):  # bounded retry (NASA rule 2)
            async with self._lock:
                now = time.monotonic()
                self._evict(now)
                tok_used = sum(t for _, t in self._tok_events)
                if len(self._req_times) < self._rpm and tok_used + est_tokens <= self._tpm:
                    self._req_times.append(now)
                    self._tok_events.append((now, est_tokens))
                    return
            await asyncio.sleep(0.05)
        raise RuntimeError("rate limiter could not admit call within bound")

    def _evict(self, now: float) -> None:
        """Drop events older than 60s. Postcondition: only last-minute events remain."""
        cutoff = now - 60.0
        self._req_times = [t for t in self._req_times if t > cutoff]
        self._tok_events = [(t, n) for (t, n) in self._tok_events if t > cutoff]
