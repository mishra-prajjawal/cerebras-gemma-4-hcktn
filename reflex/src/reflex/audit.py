"""@audited: one structured JSON record per process step. The reliability backbone."""
from __future__ import annotations
import functools
import hashlib
import json
import logging
import time
from typing import Callable, TypeVar, ParamSpec, Coroutine, Any
from pydantic import BaseModel

log = logging.getLogger("kit.audit")
T = TypeVar("T", bound=BaseModel)
P = ParamSpec("P")


def _hash(model: BaseModel) -> str:
    """Stable sha256 over canonical JSON. Precondition: model is a Pydantic model."""
    assert isinstance(model, BaseModel), "audit requires typed models"
    raw = json.dumps(model.model_dump(mode="json"), sort_keys=True).encode()
    h = hashlib.sha256(raw).hexdigest()[:16]
    assert len(h) == 16, "hash length must be exactly 16 characters"
    return h


def audited(agent: str) -> Callable[[Callable[P, Coroutine[Any, Any, T]]], Callable[P, Coroutine[Any, Any, T]]]:
    """Wrap an async step(in_model) -> out_model. Logs timing, hashes, status.
    Postcondition: always emits exactly one record; re-raises only typed errors."""
    assert agent, "agent name required"
    assert len(agent) > 0, "agent name must be non-empty"

    def deco(fn: Callable[P, Coroutine[Any, Any, T]]) -> Callable[P, Coroutine[Any, Any, T]]:
        @functools.wraps(fn)
        async def wrap(*args: object, **k: object) -> T:
            models = [x for x in args if isinstance(x, BaseModel)]
            assert models, "audited step requires a typed (BaseModel) argument"
            in_model = models[0]
            assert isinstance(in_model, BaseModel), "first arg must be a BaseModel"
            t0 = time.perf_counter()
            rec: dict[str, object] = {"agent": agent, "inputs_hash": _hash(in_model)}
            try:
                out = await fn(*args, **k)  # type: ignore[arg-type]
                rec.update(outputs_hash=_hash(out), status="ok")
                return out
            except Exception as exc:  # noqa: BLE001 - re-raised after logging
                rec.update(status="error", error=type(exc).__name__)
                raise
            finally:
                rec["latency_ms"] = round((time.perf_counter() - t0) * 1000, 2)
                log.info(json.dumps(rec, sort_keys=True))
        return wrap  # pyright: ignore[reportReturnType]
    return deco
