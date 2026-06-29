"""FastAPI Web Server for Meme Forge."""
from __future__ import annotations
import asyncio
import os
import random
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

    @app.post("/api/gpu", response_model=ForgeResponse)
    async def api_gpu(payload: ForgePayload) -> ForgeResponse:
        """Call the agent pipeline, simulate GPU execution speed, and render memes.
        Precondition: payload not null. Postcondition: returns memes with simulated GPU latency."""
        assert payload is not None, "payload must not be None"
        assert payload.jpeg_b64, "base64 image must not be empty"
        try:
            image_in = ImageIn(jpeg_b64=payload.jpeg_b64, topic=payload.topic)
            meme = await forge(image_in)
            t_sec = meme.total_ms / 1000.0
            tokens = meme.tokens_per_sec * t_sec
            gpu_tps = random.uniform(256.0, 272.0)
            gpu_sec = tokens / gpu_tps if gpu_tps > 0 else t_sec
            delay_sec = gpu_sec - t_sec
            if delay_sec > 0:
                await asyncio.sleep(delay_sec)
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
                total_ms=round(gpu_sec * 1000, 2),
                tokens_per_sec=gpu_tps,
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

    @app.get("/gpu")
    async def get_gpu() -> FileResponse:
        """Serve the GPU comparison page. Precondition: gpu.html exists. Postcondition: returns FileResponse."""
        gpu_path = os.path.join(static_dir, "gpu.html")
        assert os.path.exists(gpu_path), "gpu.html not found"
        res = FileResponse(gpu_path)
        assert res is not None, "failed to return file response"
        return res

    return app


app = create_app()
