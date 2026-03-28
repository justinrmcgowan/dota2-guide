"""Session sync endpoint for state durability across browser changes.

Stores a single active match session JSON blob. The frontend can POST
its current state periodically and GET it back on a fresh browser load
if localStorage is empty. Per D-02: secondary to localStorage, used for
multi-device and browser-change scenarios.
"""

from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter()

# In-memory single-session store. Survives container restarts only if
# the container isn't recreated. For V1 single-user this is acceptable.
_session_data: dict | None = None


class SessionPayload(BaseModel):
    """Flexible session blob -- frontend defines the shape."""

    match_id: str | None = None
    game_state: dict  # The full serialized game store state
    recommendations: dict | None = None  # Serialized recommendation store state
    saved_at: float  # Unix timestamp from frontend


@router.post("/session")
async def save_session(payload: SessionPayload):
    """Save current match session state.

    Called periodically by the frontend (e.g., every 60s during active game)
    to sync state for durability. Only the latest session is stored.
    Per D-10: one active session at a time.
    """
    global _session_data
    _session_data = payload.model_dump()
    return {"status": "ok", "saved_at": payload.saved_at}


@router.get("/session")
async def get_session():
    """Retrieve the last saved session state.

    Returns the session blob or null if no session exists.
    The frontend checks this on startup if localStorage is empty.
    """
    if _session_data is None:
        return {"session": None}
    return {"session": _session_data}


@router.delete("/session")
async def clear_session():
    """Clear the stored session (called on new game detection or manual reset)."""
    global _session_data
    _session_data = None
    return {"status": "ok"}
