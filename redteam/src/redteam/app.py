"""Red-Team entrypoint: text file path -> printed verdict, or starts the web server."""
from __future__ import annotations
import asyncio
import sys
from .contracts import DocIn
from .pipeline import review


async def main(doc_path: str) -> None:
    """Precondition: a readable text path. Postcondition: prints the verdict."""
    assert doc_path, "document path required"
    with open(doc_path, "r", encoding="utf-8") as fh:
        text = fh.read()
    verdict, ms, _, _, _ = await review(DocIn(text=text))
    assert verdict is not None, "verdict must be returned"
    print("overall_risk=" + verdict.overall_risk + "  committee_ms=" + str(ms))
    print(verdict.summary)
    for b in verdict.blocking_issues:
        print("  - BLOCK: " + b)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        import uvicorn
        uvicorn.run("redteam.server:app", host="0.0.0.0", port=8000, reload=True)
    elif len(sys.argv) > 1:
        asyncio.run(main(sys.argv[1]))
    else:
        import uvicorn
        print("No document path provided. Launching Red-Team Committee Web UI...")
        uvicorn.run("redteam.server:app", host="0.0.0.0", port=8000)
