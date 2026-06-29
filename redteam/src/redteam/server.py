"""FastAPI server for the Red-Team Committee Web UI."""
from __future__ import annotations
import base64
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from .contracts import DocIn, Verdict, ReviewerReport
from .pipeline import review

# Setup logger
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("redteam.server")

app = FastAPI(title="Red-Team Committee Web API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ReviewResponse(BaseModel):
    """Web response contract enclosing verdict, reviewer reports, and telemetry."""
    verdict: Verdict
    reports: list[ReviewerReport]
    doc_text: str
    latency_ms: float
    tokens_per_sec: float


@app.post("/api/review", response_model=ReviewResponse)
async def api_review(file: UploadFile = File(...)) -> ReviewResponse:
    """Precondition: file must be sent. Postcondition: returns validated ReviewResponse."""
    assert file is not None, "uploaded file must be provided"
    assert file.filename, "uploaded file must have a filename"

    filename = file.filename.lower()
    content = await file.read()

    # 1. Parse into DocIn based on file type
    if filename.endswith((".png", ".jpg", ".jpeg")):
        b64_str = base64.b64encode(content).decode("utf-8")
        doc = DocIn(jpeg_b64=b64_str)
    else:
        try:
            text_content = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise HTTPException(
                status_code=400,
                detail="Only UTF-8 encoded text files or images are supported."
            ) from exc
        doc = DocIn(text=text_content)

    # 2. Run the review pipeline
    try:
        verdict, ms, text, reports, tps = await review(doc)
    except Exception as exc:
        log.exception("Pipeline review failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    # 3. Create response
    response = ReviewResponse(
        verdict=verdict,
        reports=reports,
        doc_text=text,
        latency_ms=ms,
        tokens_per_sec=tps
    )
    assert isinstance(response, ReviewResponse), "output must be ReviewResponse"
    assert response.latency_ms >= 0.0, "latency must be non-negative"
    return response


# Mount static files to serve the frontend
app.mount("/", StaticFiles(directory="src/redteam/static", html=True), name="static")
