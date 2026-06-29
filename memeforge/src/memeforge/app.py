"""Meme Forge entrypoint: image path -> ranked captions printed to stdout."""
from __future__ import annotations
import asyncio
import base64
import sys
from .contracts import ImageIn
from .pipeline import forge


async def main(image_path: str, topic: str = "") -> None:
    """Precondition: a readable image path. Postcondition: prints top captions."""
    assert image_path, "image path required"
    with open(image_path, "rb") as fh:
        b64 = base64.b64encode(fh.read()).decode()
    meme = await forge(ImageIn(jpeg_b64=b64, topic=topic))
    assert meme is not None, "pipeline failed to return a Meme object"
    assert len(meme.top) > 0, "no ranked captions returned"
    print("writers=" + str(meme.writers) + "  total_ms=" + str(meme.total_ms)
          + "  tok/s=" + str(meme.tokens_per_sec))
    for i, rc in enumerate(meme.top):
        print(str(i + 1) + ". [" + str(rc.score) + "] " + rc.text)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        import uvicorn
        uvicorn.run("memeforge.web:app", host="0.0.0.0", port=8001, reload=True)
    elif len(sys.argv) == 1:
        print("No image path provided. Starting web server on http://localhost:8001 ...")
        import uvicorn
        uvicorn.run("memeforge.web:app", host="0.0.0.0", port=8001)
    else:
        asyncio.run(main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else ""))

