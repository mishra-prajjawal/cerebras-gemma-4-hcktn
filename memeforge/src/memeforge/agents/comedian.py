from ..audit import audited
from ..config import get_settings
from ..contracts import CaptionSet, ImageIn
from .base import Agent
from ..cerebras_client import CerebrasClient


class Comedian(Agent[ImageIn, CaptionSet]):
    """One persona, several captions, a single multimodal call."""

    def __init__(self, client: CerebrasClient, persona: str) -> None:
        super().__init__(client)
        assert persona, "persona required"
        self.persona = persona
        self.name = "comedian"

    @audited("comedian")
    async def run(self, data: ImageIn) -> CaptionSet:
        """Precondition: ImageIn. Postcondition: validated CaptionSet in this persona."""
        assert isinstance(data, ImageIn), "comedian input must be ImageIn"
        s = get_settings()
        topic = data.topic or "general internet humor"
        system = (
            "You are " + self.persona + ", a meme caption writer. Look at the image and "
            "write short, punchy, screenshot-ready captions about: " + topic + ". Be "
            "original and funny, never hateful or offensive. Return 3 to 5 captions."
        )
        url = "data:image/jpeg;base64," + data.jpeg_b64
        messages: list[dict[str, object]] = [
            {"role": "system", "content": system},
            {"role": "user", "content": [
                {"type": "text", "text": "Caption this image in your voice."},
                {"type": "image_url", "image_url": {"url": url}},
            ]},
        ]
        out = await self._client.structured(
            messages=messages, out=CaptionSet, max_tokens=s.caption_max_tokens)
        assert out.captions, "comedian returned no captions"
        return out
