import asyncio
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Set mock API key before importing client/config
os.environ["CEREBRAS_API_KEY"] = "csk-mockkey123456"

from reflex.cerebras_client import CerebrasClient
from reflex.contracts import ErrorReport, Strict


class MockModel(Strict):
    field_a: str
    field_b: int


@pytest.mark.asyncio
async def test_schema_generation() -> None:
    # Test that iterative schema works and sets additionalProperties=False
    schema_wrapper = CerebrasClient._schema(MockModel)
    assert schema_wrapper["type"] == "json_schema"
    
    js = schema_wrapper["json_schema"]["schema"]
    assert js["additionalProperties"] is False
    assert js["properties"]["field_a"]["type"] == "string"


@pytest.mark.asyncio
async def test_structured_success() -> None:
    with patch("reflex.cerebras_client.AsyncOpenAI") as mock_openai_class:
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_resp = MagicMock()
        mock_resp.choices = [
            MagicMock(message=MagicMock(content='{"status": "ok", "deviation": "none", "severity": 0, "fix_hint": "none"}'))
        ]
        mock_resp.usage = MagicMock(completion_tokens=50)
        
        mock_client.chat.completions.create = AsyncMock(return_value=mock_resp)
        
        client = CerebrasClient()
        report = await client.structured(
            messages=[{"role": "user", "content": "hello"}],
            out=ErrorReport
        )
        
        assert isinstance(report, ErrorReport)
        assert report.status == "ok"
        assert report.severity == 0
        assert client.last_tokens_per_sec > 0.0
