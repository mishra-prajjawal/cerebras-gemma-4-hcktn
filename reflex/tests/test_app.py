import os
import pytest
from fastapi.testclient import TestClient

# Setup mock key before importing client/config
os.environ["CEREBRAS_API_KEY"] = "csk-mockkey123456"

from reflex.app import app, get_default_steps


def test_get_default_steps() -> None:
    steps = get_default_steps()
    assert len(steps) == 3
    assert steps[0].title == "Insert Blue Battery Pack"


def test_index_route() -> None:
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "REFLEX" in response.text
    assert "MULTI-AGENT SWARM" in response.text


def test_websocket_connection_handshake() -> None:
    client = TestClient(app)
    # Validate we can connect and perform handshake
    with client.websocket_connect("/ws/stream") as websocket:
        # Just establish connection and close immediately
        assert websocket is not None
