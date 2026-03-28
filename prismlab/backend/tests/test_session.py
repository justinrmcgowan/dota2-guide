"""Tests for session sync endpoint (POST/GET/DELETE /api/session)."""

import pytest

from api.routes.session import _session_data
import api.routes.session as session_module


@pytest.mark.asyncio
async def test_get_session_empty(test_client):
    """GET /api/session returns null session when nothing is stored."""
    # Ensure clean state
    session_module._session_data = None

    response = await test_client.get("/api/session")
    assert response.status_code == 200
    assert response.json() == {"session": None}


@pytest.mark.asyncio
async def test_save_and_get_session(test_client):
    """POST a session payload, then GET it back -- verify round-trip."""
    session_module._session_data = None

    payload = {
        "match_id": "12345",
        "game_state": {"hero": "Anti-Mage", "role": 1},
        "recommendations": {"items": ["bfury"]},
        "saved_at": 1700000000.0,
    }

    # Save
    response = await test_client.post("/api/session", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["saved_at"] == 1700000000.0

    # Retrieve
    response = await test_client.get("/api/session")
    assert response.status_code == 200
    session = response.json()["session"]
    assert session["match_id"] == "12345"
    assert session["game_state"] == {"hero": "Anti-Mage", "role": 1}
    assert session["recommendations"] == {"items": ["bfury"]}
    assert session["saved_at"] == 1700000000.0


@pytest.mark.asyncio
async def test_save_overwrites_previous(test_client):
    """POST two sessions, GET returns only the latest."""
    session_module._session_data = None

    first = {
        "match_id": "111",
        "game_state": {"hero": "Axe"},
        "saved_at": 1700000001.0,
    }
    second = {
        "match_id": "222",
        "game_state": {"hero": "Crystal Maiden"},
        "saved_at": 1700000002.0,
    }

    await test_client.post("/api/session", json=first)
    await test_client.post("/api/session", json=second)

    response = await test_client.get("/api/session")
    session = response.json()["session"]
    assert session["match_id"] == "222"
    assert session["game_state"]["hero"] == "Crystal Maiden"


@pytest.mark.asyncio
async def test_clear_session(test_client):
    """POST a session, DELETE /api/session, GET returns null."""
    session_module._session_data = None

    payload = {
        "match_id": "999",
        "game_state": {"hero": "Pudge"},
        "saved_at": 1700000003.0,
    }
    await test_client.post("/api/session", json=payload)

    # Clear
    response = await test_client.delete("/api/session")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    # Verify cleared
    response = await test_client.get("/api/session")
    assert response.json() == {"session": None}


@pytest.mark.asyncio
async def test_save_session_validation(test_client):
    """POST with missing required field game_state returns 422."""
    session_module._session_data = None

    # Missing game_state and saved_at
    response = await test_client.post(
        "/api/session",
        json={"match_id": "123"},
    )
    assert response.status_code == 422
