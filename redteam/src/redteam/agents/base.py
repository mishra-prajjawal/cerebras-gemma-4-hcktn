"""Agent ABC: a typed, audited, single-purpose async step."""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Coroutine, Generic, TypeVar
from pydantic import BaseModel
from ..cerebras_client import CerebrasClient

I = TypeVar("I", bound=BaseModel)  # noqa: E741
O = TypeVar("O", bound=BaseModel)  # noqa: E741


class Agent(ABC, Generic[I, O]):
    """One responsibility. run() is wrapped by @audited in the concrete class."""
    name: str

    def __init__(self, client: CerebrasClient) -> None:
        assert client is not None, "agent requires a shared client"
        self._client = client

    @abstractmethod
    def run(self, data: I) -> Coroutine[Any, Any, O]: ...
