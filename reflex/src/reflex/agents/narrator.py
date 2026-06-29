from __future__ import annotations
from ..cerebras_client import CerebrasClient
from ..contracts import Coaching
from .base import Agent
from ..audit import audited

_SYS = ("You are an assembly narrator. Your job is to take the Coaching instruction and polish the "
        "spoken voice text ('say') to make it sound perfectly natural, engaging, and professional when read out loud. "
        "Keep it concise (1-2 sentences). Do not alter the focus step index.")


class Narrator(Agent[Coaching, Coaching]):
    name = "narrator"

    def __init__(self, client: CerebrasClient) -> None:
        super().__init__(client)
        assert client is not None, "client is required"
        assert isinstance(client, CerebrasClient), "client must be a CerebrasClient"

    @audited("narrator")
    async def run(self, data: Coaching) -> Coaching:
        """Precondition: data is Coaching. Postcondition: validated polished Coaching."""
        assert isinstance(data, Coaching), "input must be a Coaching model"
        assert len(data.say) > 0, "instruction to narrate must be non-empty"
        
        messages: list[dict[str, object]] = [
            {"role": "system", "content": _SYS},
            {"role": "user", "content": f"Polishing instruction: {data.say}"}
        ]
        
        res = await self._client.structured(
            messages=messages, out=Coaching, max_tokens=256)
        
        res.show_step_idx = data.show_step_idx
        assert isinstance(res, Coaching), "result must be a Coaching model"
        return res
