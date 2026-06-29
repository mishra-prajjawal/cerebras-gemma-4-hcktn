"""Perceptor agent (stub). TODO(agent): implement per CLAUDE.md + skills."""
from __future__ import annotations
from ..audit import audited
from ..contracts import Frame, Observation
from .base import Agent


from ..cerebras_client import CerebrasClient

_SYS = ("You are a physical assembly perceptor. Scan the workbench image and list the visible "
        "components, tools, and materials. Provide a brief summary of the layout. "
        "Respond ONLY in the structured JSON format.")


class Perceptor(Agent[Frame, Observation]):
    name = "perceptor"

    def __init__(self, client: CerebrasClient) -> None:
        super().__init__(client)
        assert client is not None, "client is required"
        assert isinstance(client, CerebrasClient), "client must be a CerebrasClient"

    @audited("perceptor")
    async def run(self, data: Frame) -> Observation:
        """Precondition: data is a Frame. Postcondition: a validated Observation."""
        assert isinstance(data, Frame), "input must be a Frame"
        url = f"data:image/jpeg;base64,{data.jpeg_b64}"
        messages: list[dict[str, object]] = [
            {"role": "system", "content": _SYS},
            {"role": "user", "content": [
                {"type": "text", "text": "Describe everything currently on the workbench."},
                {"type": "image_url", "image_url": {"url": url}},
            ]},
        ]
        obs = await self._client.structured(
            messages=messages, out=Observation, max_tokens=384)
        assert 0.0 <= obs.confidence <= 1.0, "confidence out of range"
        assert len(obs.summary) > 0, "summary cannot be empty"
        return obs
