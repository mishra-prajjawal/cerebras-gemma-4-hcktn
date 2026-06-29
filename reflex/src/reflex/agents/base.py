"""Agent ABC: a typed, audited, single-purpose async step."""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Coroutine, Any
from pydantic import BaseModel
from ..cerebras_client import CerebrasClient

InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)


class Agent(ABC, Generic[InputT, OutputT]):
    """One responsibility. run() is wrapped by @audited in the concrete class."""
    name: str

    def __init__(self, client: CerebrasClient) -> None:
        assert client is not None, "agent requires a shared client"
        assert isinstance(client, CerebrasClient), "client must be a CerebrasClient"
        self._client = client

    @abstractmethod
    def run(self, data: InputT) -> Coroutine[Any, Any, OutputT]: ...
