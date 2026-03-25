"""WebSocket ConnectionManager with throttled broadcast loop.

Manages client WebSocket connections and runs a background 1Hz broadcast
loop that pushes game state only when data has changed since last push.
Dead connections are cleaned up without blocking other clients.
"""

import asyncio
import json
import logging

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WSManager:
    """Manages WebSocket client connections and throttled state broadcast."""

    def __init__(self) -> None:
        self.connections: list[WebSocket] = []
        self._broadcast_task: asyncio.Task | None = None
        self._last_sent_hash: int = 0

    async def connect(self, ws: WebSocket) -> None:
        """Accept and register a new WebSocket client."""
        await ws.accept()
        self.connections.append(ws)
        logger.info(f"WebSocket client connected. Total: {len(self.connections)}")

    def disconnect(self, ws: WebSocket) -> None:
        """Remove a WebSocket client from the connections list."""
        if ws in self.connections:
            self.connections.remove(ws)
        logger.info(f"WebSocket client disconnected. Total: {len(self.connections)}")

    async def start_broadcast_loop(self, state_manager) -> None:  # type: ignore[no-untyped-def]
        """Background task: check state every 1s, broadcast if changed.

        This is the throttle point -- GSI sends at ~2Hz, we aggregate and
        push at max 1Hz only when the data has actually changed.
        """
        while True:
            await asyncio.sleep(1.0)
            state_dict = state_manager.to_broadcast_dict()
            if state_dict is None:
                continue
            msg = json.dumps({"type": "game_state", "data": state_dict})
            msg_hash = hash(msg)
            if msg_hash == self._last_sent_hash:
                continue
            self._last_sent_hash = msg_hash
            await self._broadcast(msg)

    async def _broadcast(self, message: str) -> None:
        """Send message to all connected clients, removing dead ones."""
        dead: list[WebSocket] = []
        for ws in self.connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            if ws in self.connections:
                self.connections.remove(ws)


# Module-level singleton
ws_manager = WSManager()
