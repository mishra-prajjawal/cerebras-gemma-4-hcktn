from __future__ import annotations
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from memeforge.contracts import Meme, RankedCaption
from memeforge.web import app


def test_web_index() -> None:
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200, "failed to load index.html"
    assert "Meme Forge" in response.text, "index page title or headers missing"
    assert "dropzone" in response.text, "index page dropzone missing"


@pytest.mark.anyio
async def test_web_api_forge() -> None:
    client = TestClient(app)
    mock_meme = Meme(
        topic="testing",
        top=[RankedCaption(text="test caption", score=90, reason="test reason")],
        writers=6,
        total_ms=500.0,
        tokens_per_sec=1200.0
    )
    with patch("memeforge.web.forge", new_callable=AsyncMock) as mock_forge, \
         patch("memeforge.web.overlay", return_value="mocked_image_b64") as mock_overlay:
        mock_forge.return_value = mock_meme
        payload = {"jpeg_b64": "dGVzdA==", "topic": "testing"}
        response = client.post("/api/forge", json=payload)
        assert response.status_code == 200, "forge api returned error status"
        data = response.json()
        assert data["topic"] == "testing", "steer topic was changed"
        assert data["writers"] == 6, "mismatched writers count"
        assert data["total_ms"] == 500.0, "mismatched latency metric"
        assert data["tokens_per_sec"] == 1200.0, "mismatched throughput metric"
        assert len(data["top"]) == 1, "top meme count incorrect"
        assert data["top"][0]["text"] == "test caption", "meme text changed"
        assert data["top"][0]["image_b64"] == "mocked_image_b64", "meme overlay image missing"
        mock_forge.assert_called_once()
        mock_overlay.assert_called_once_with("dGVzdA==", mock_meme.top[0])


@pytest.mark.anyio
async def test_web_api_gpu() -> None:
    client = TestClient(app)
    mock_meme = Meme(
        topic="testing",
        top=[RankedCaption(text="test caption", score=90, reason="test reason")],
        writers=6,
        total_ms=100.0,
        tokens_per_sec=1000.0
    )
    with patch("memeforge.web.forge", new_callable=AsyncMock) as mock_forge, \
         patch("memeforge.web.overlay", return_value="mocked_image_b64") as mock_overlay:
        mock_forge.return_value = mock_meme
        payload = {"jpeg_b64": "dGVzdA==", "topic": "testing"}
        response = client.post("/api/gpu", json=payload)
        assert response.status_code == 200, "gpu api returned error status"
        data = response.json()
        assert 256.0 <= data["tokens_per_sec"] <= 272.0, "simulated throughput out of range 256-272 Tok/s"
        expected_sec = 100.0 / data["tokens_per_sec"]
        assert data["total_ms"] == round(expected_sec * 1000, 2), "mismatched simulated GPU latency"
        assert len(data["top"]) == 1, "top meme count incorrect"
        mock_forge.assert_called_once()
        mock_overlay.assert_called_once_with("dGVzdA==", mock_meme.top[0])


def test_web_gpu_page() -> None:
    client = TestClient(app)
    response = client.get("/gpu")
    assert response.status_code == 200, "failed to load gpu.html"
    assert "Meme Forge" in response.text, "gpu page title or headers missing"
    assert "Emulated" in response.text or "emulated" in response.text, "gpu page does not mention emulated speed difference"

