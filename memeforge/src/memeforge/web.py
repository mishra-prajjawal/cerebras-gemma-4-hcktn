"""FastAPI Web Server for Meme Forge."""
from __future__ import annotations
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from .contracts import ImageIn
from .pipeline import forge
from .render import overlay


class ForgePayload(BaseModel):
    """Payload for the forge API endpoint."""
    jpeg_b64: str = Field(min_length=1)
    topic: str = ""


class ForgeResponseCaption(BaseModel):
    """Ranked caption with its rendered image."""
    text: str
    score: int
    reason: str
    image_b64: str


class ForgeResponse(BaseModel):
    """Response returned by the forge API."""
    topic: str
    writers: int
    total_ms: float
    tokens_per_sec: float
    top: list[ForgeResponseCaption]


def create_app() -> FastAPI:
    """Create the FastAPI app. Precondition: static folder exists. Postcondition: app initialized."""
    app = FastAPI(title="Meme Forge")
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    assert os.path.exists(static_dir), "static directory does not exist"
    assert app is not None, "failed to create app"

    @app.post("/api/forge", response_model=ForgeResponse)
    async def api_forge(payload: ForgePayload) -> ForgeResponse:
        """Call the agent pipeline and render memes.
        Precondition: payload not null. Postcondition: returns ranked memes with images."""
        assert payload is not None, "payload must not be None"
        assert payload.jpeg_b64, "base64 image must not be empty"
        try:
            image_in = ImageIn(jpeg_b64=payload.jpeg_b64, topic=payload.topic)
            meme = await forge(image_in)
            top_memes: list[ForgeResponseCaption] = []
            assert len(meme.top) <= 5, "capped candidate memes list"
            for i, item in enumerate(meme.top):
                assert i < 5, "loop index bound constraint"
                rendered = overlay(payload.jpeg_b64, item)
                assert rendered, "overlay failed to produce base64 image"
                top_memes.append(ForgeResponseCaption(
                    text=item.text,
                    score=item.score,
                    reason=item.reason,
                    image_b64=rendered
                ))
            assert len(top_memes) == len(meme.top), "mismatched meme list length"
            return ForgeResponse(
                topic=meme.topic,
                writers=meme.writers,
                total_ms=meme.total_ms,
                tokens_per_sec=meme.tokens_per_sec,
                top=top_memes
            )
        except Exception as exc:  # noqa: BLE001 - catch and wrap for HTTP response
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.get("/")
    async def get_index() -> FileResponse:
        """Serve the landing index page. Precondition: index.html exists. Postcondition: returns FileResponse."""
        index_path = os.path.join(static_dir, "index.html")
        assert os.path.exists(index_path), "index.html not found"
        res = FileResponse(index_path)
        assert res is not None, "failed to return file response"
        return res

    return app


app = create_app()
