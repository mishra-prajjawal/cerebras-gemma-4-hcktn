import os
import pytest
from fastapi.testclient import TestClient

# Setup mock key before importing client/config
os.environ["CEREBRAS_API_KEY"] = "csk-mockkey123456"

from reflex.app import app, get_default_steps


def test_get_default_steps() -> None:
    steps = get_default_steps()
    assert len(steps) == 3
    assert steps[0].title == "Clear Desk Workspace"


def test_index_route() -> None:
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "REFLEX" in response.text
    assert "MULTI-AGENT SWARM" in response.text.upper()


def test_simulate_correct() -> None:
    client = TestClient(app)
    response = client.post("/api/simulate", json={"step_idx": 0, "mistake": False})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert len(data["say"]) > 0
    assert data["step_idx"] == 1


def test_simulate_mistake() -> None:
    client = TestClient(app)
    response = client.post("/api/simulate", json={"step_idx": 1, "mistake": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert len(data["say"]) > 0
    assert data["step_idx"] == 1
