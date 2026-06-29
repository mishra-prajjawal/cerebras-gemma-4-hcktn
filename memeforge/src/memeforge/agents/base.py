"""Agent ABC: a typed, audited, single-purpose async step."""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Awaitable, Generic, TypeVar
from pydantic import BaseModel
from ..cerebras_client import CerebrasClient

InT = TypeVar("InT", bound=BaseModel)
OutT = TypeVar("OutT", bound=BaseModel)


class Agent(ABC, Generic[InT, OutT]):
    """One responsibility. run() is wrapped by @audited in the concrete class."""
    name: str

    def __init__(self, client: CerebrasClient) -> None:
        assert client is not None, "agent requires a shared client"
        self._client = client

    @abstractmethod
    def run(self, data: InT) -> Awaitable[OutT]: ...


