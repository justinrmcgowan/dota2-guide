"""Tests for WebSocket ConnectionManager with throttled broadcast.

Tests cover: connect/disconnect, change-detection broadcast,
dead connection cleanup, and /ws endpoint integration.
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gsi.ws_manager import WSManager


# ---------------------------------------------------------------------------
# Unit tests for WSManager
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_connect_adds_websocket():
    """WSManager.connect() adds a WebSocket to the connections list."""
    mgr = WSManager()
    ws = AsyncMock()
    await mgr.connect(ws)
    assert ws in mgr.connections
    assert len(mgr.connections) == 1
    ws.accept.assert_awaited_once()


@pytest.mark.asyncio
async def test_disconnect_removes_websocket():
    """WSManager.disconnect() removes a WebSocket from the connections list."""
    mgr = WSManager()
    ws = AsyncMock()
    await mgr.connect(ws)
    assert len(mgr.connections) == 1
    mgr.disconnect(ws)
    assert ws not in mgr.connections
    assert len(mgr.connections) == 0


@pytest.mark.asyncio
async def test_disconnect_ignores_unknown_websocket():
    """WSManager.disconnect() does not raise for unknown WebSocket."""
    mgr = WSManager()
    ws = AsyncMock()
    # Should not raise
    mgr.disconnect(ws)
    assert len(mgr.connections) == 0


@pytest.mark.asyncio
async def test_broadcast_sends_when_state_changed():
    """Broadcast loop sends state when to_broadcast_dict() returns new data."""
    mgr = WSManager()
    ws = AsyncMock()
    await mgr.connect(ws)

    state_data = {"hero_name": "antimage", "gold": 500}
    state_manager = MagicMock()
    state_manager.to_broadcast_dict.return_value = state_data

    # Run one iteration of broadcast loop (patch sleep to avoid delay)
    iteration_count = 0

    async def fake_sleep(duration):
        nonlocal iteration_count
        iteration_count += 1
        if iteration_count > 1:
            raise asyncio.CancelledError()

    with patch("gsi.ws_manager.asyncio.sleep", side_effect=fake_sleep):
        try:
            await mgr.start_broadcast_loop(state_manager)
        except asyncio.CancelledError:
            pass

    # Should have sent the state
    ws.send_text.assert_awaited_once()
    sent_msg = ws.send_text.call_args[0][0]
    parsed = json.loads(sent_msg)
    assert parsed["type"] == "game_state"
    assert parsed["data"] == state_data


@pytest.mark.asyncio
async def test_broadcast_skips_when_state_unchanged():
    """Broadcast loop does NOT send when state has not changed (hash match)."""
    mgr = WSManager()
    ws = AsyncMock()
    await mgr.connect(ws)

    state_data = {"hero_name": "antimage", "gold": 500}
    state_manager = MagicMock()
    state_manager.to_broadcast_dict.return_value = state_data

    iteration_count = 0

    async def fake_sleep(duration):
        nonlocal iteration_count
        iteration_count += 1
        if iteration_count > 2:
            raise asyncio.CancelledError()

    with patch("gsi.ws_manager.asyncio.sleep", side_effect=fake_sleep):
        try:
            await mgr.start_broadcast_loop(state_manager)
        except asyncio.CancelledError:
            pass

    # State returned twice but identical -- should only send ONCE
    assert ws.send_text.await_count == 1


@pytest.mark.asyncio
async def test_broadcast_skips_when_state_is_none():
    """Broadcast loop does NOT send when to_broadcast_dict() returns None."""
    mgr = WSManager()
    ws = AsyncMock()
    await mgr.connect(ws)

    state_manager = MagicMock()
    state_manager.to_broadcast_dict.return_value = None

    iteration_count = 0

    async def fake_sleep(duration):
        nonlocal iteration_count
        iteration_count += 1
        if iteration_count > 1:
            raise asyncio.CancelledError()

    with patch("gsi.ws_manager.asyncio.sleep", side_effect=fake_sleep):
        try:
            await mgr.start_broadcast_loop(state_manager)
        except asyncio.CancelledError:
            pass

    ws.send_text.assert_not_awaited()


@pytest.mark.asyncio
async def test_dead_connections_removed_during_broadcast():
    """Dead connections are removed during broadcast without raising."""
    mgr = WSManager()

    good_ws = AsyncMock()
    dead_ws = AsyncMock()
    dead_ws.send_text.side_effect = Exception("Connection closed")

    await mgr.connect(good_ws)
    await mgr.connect(dead_ws)
    assert len(mgr.connections) == 2

    state_data = {"hero_name": "axe", "gold": 300}
    state_manager = MagicMock()
    state_manager.to_broadcast_dict.return_value = state_data

    iteration_count = 0

    async def fake_sleep(duration):
        nonlocal iteration_count
        iteration_count += 1
        if iteration_count > 1:
            raise asyncio.CancelledError()

    with patch("gsi.ws_manager.asyncio.sleep", side_effect=fake_sleep):
        try:
            await mgr.start_broadcast_loop(state_manager)
        except asyncio.CancelledError:
            pass

    # Dead ws should be removed, good ws should remain
    assert dead_ws not in mgr.connections
    assert good_ws in mgr.connections
    assert len(mgr.connections) == 1
    # Good ws should have received the message
    good_ws.send_text.assert_awaited_once()


# ---------------------------------------------------------------------------
# Integration test for /ws endpoint
# ---------------------------------------------------------------------------

def test_websocket_endpoint_accepts_connection():
    """WebSocket endpoint /ws accepts connections via Starlette TestClient."""
    from starlette.testclient import TestClient
    from main import app

    client = TestClient(app)
    with client.websocket_connect("/ws") as ws:
        # Connection established -- just verify we can connect
        # We don't expect any messages without GSI data flowing
        pass
    # If we get here without exception, the connection was accepted
