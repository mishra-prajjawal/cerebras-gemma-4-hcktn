import os
import pytest
from reflex.cerebras_client import CerebrasClient
from reflex.contracts import ErrorReport


@pytest.mark.asyncio
async def test_real_cerebras_call_if_key_exists() -> None:
    api_key = os.environ.get("CEREBRAS_API_KEY", "")
    if not api_key or api_key.startswith("csk-mock") or api_key == "csk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx":
        pytest.skip("CEREBRAS_API_KEY not set or is placeholder; skipping real API call.")
        return

    # Initialize the client (will use CEREBRAS_API_KEY from environment)
    client = CerebrasClient()
    
    messages = [
        {"role": "system", "content": "You are a QA assistant. Analyze the description and output an ErrorReport."},
        {"role": "user", "content": "The worker forgot to screw in the main bolt on step 2."}
    ]
    
    report = await client.structured(
        messages=messages,
        out=ErrorReport,
        max_tokens=256
    )
    
    assert isinstance(report, ErrorReport)
    assert report.status in ("ok", "warn", "error")
    assert 0 <= report.severity <= 5
    assert len(report.deviation) > 0
    assert len(report.fix_hint) > 0
