"""Async client for Cerebras via its OpenAI-compatible endpoint.

Provider-agnostic: only base_url + model_id change to move providers. Rate-gated,
retried, strict-schema (generated from the Pydantic model), and timing-aware.
Docs: https://inference-docs.cerebras.ai/resources/openai
"""
from __future__ import annotations
import asyncio
import random
import time
from typing import Any, cast, Type, TypeVar
from openai import AsyncOpenAI
from pydantic import BaseModel
from .config import get_settings
from .rate_limiter import RateLimiter
from .contracts import Strict

T = TypeVar("T", bound=BaseModel)
_MAX_RETRIES = 4


class CerebrasClient:
    """Single shared client over the OpenAI-compatible Cerebras endpoint."""

    def __init__(self) -> None:
        s = get_settings()
        self._s = s
        self._client = AsyncOpenAI(api_key=s.cerebras_api_key, base_url=s.base_url)
        self._limiter = RateLimiter(s.max_rpm, s.max_tpm)
        self._sema = asyncio.Semaphore(s.max_concurrency)
        self.last_tokens_per_sec: float = 0.0

    @staticmethod
    def _schema(model: Type[T]) -> dict[str, object]:
        """Build a strict json_schema FROM the Pydantic model (no drift).
        Cerebras strict mode requires additionalProperties:false on every object."""
        assert model is not None, "model cannot be None"
        js = model.model_json_schema()
        assert js is not None, "json schema generation failed"
        stack: list[dict[str, object]] = [js]
        for _ in range(1000):
            if not stack:
                break
            curr = stack.pop()
            if isinstance(curr, dict):
                curr.pop("minItems", None)
                curr.pop("maxItems", None)
                curr.pop("minLength", None)
                curr.pop("maxLength", None)
                curr.pop("minimum", None)
                curr.pop("maximum", None)
                if curr.get("type") == "object":
                    curr["additionalProperties"] = False
                for val in curr.values():
                    if isinstance(val, dict):
                        stack.append(val)
                    elif isinstance(val, list):
                        for item in val:
                            if isinstance(item, dict):
                                stack.append(item)
        assert not stack, "schema cleaning stack should be empty"
        return {"type": "json_schema",
                "json_schema": {"name": model.__name__, "strict": True, "schema": js}}

    async def structured(self, *, messages: list[dict[str, object]], out: Type[T],
                         reasoning_effort: str = "none", max_tokens: int = 512) -> T:
        """Call the model and return a validated `out`. Retries on transient errors.
        Precondition: out is a Strict model. Postcondition: result validates or raises."""
        assert issubclass(out, Strict), "structured output must be a Strict model"
        assert messages, "messages must be non-empty"
        est = 256 + max_tokens
        for attempt in range(_MAX_RETRIES):
            await self._limiter.acquire(est)
            t0 = time.perf_counter()
            try:
                async with self._sema:
                    resp = await self._client.chat.completions.create(
                        model=self._s.model_id,
                        messages=cast(Any, messages),
                        max_completion_tokens=max_tokens,
                        response_format=cast(Any, self._schema(out)),
                        extra_body={"reasoning_effort": reasoning_effort})
                self._record_timing(resp, time.perf_counter() - t0)
                content = resp.choices[0].message.content or ""
                assert content, "empty completion content"
                return out.model_validate_json(content)
            except Exception:  # noqa: BLE001 - retried below or re-raised
                if attempt == _MAX_RETRIES - 1:
                    raise
                await asyncio.sleep((2 ** attempt) * 0.2 + random.random() * 0.1)
        raise RuntimeError("unreachable: retry loop exhausted")

    def _record_timing(self, resp: object, wall_s: float) -> None:
        """Compute tokens/sec from usage + wall time. Best-effort; never raises."""
        try:
            usage = getattr(resp, "usage", None)
            ct = float(getattr(usage, "completion_tokens", 0) or 0)
            self.last_tokens_per_sec = ct / (wall_s or 1e-6)
        except Exception:  # noqa: BLE001 - telemetry must not break the hot path
            self.last_tokens_per_sec = 0.0
