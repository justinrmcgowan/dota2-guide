"""POST /gsi endpoint: receives Dota 2 Game State Integration data.

Dota 2 sends HTTP POST requests with JSON body at ~2Hz. This endpoint
validates the auth token, parses the payload via GsiStateManager, and
always returns HTTP 200 (even on parse errors) to keep Dota 2's delta
tracking working.
"""

import logging

from fastapi import APIRouter, Request, Response

from config import settings
from gsi.state_manager import gsi_state_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/gsi")
async def receive_gsi(request: Request) -> Response:
    """Receive Dota 2 Game State Integration data.

    Always returns HTTP 200 so Dota 2 continues sending delta fields
    (previously, added). Only returns 401 if auth token is configured
    and the payload's auth.token doesn't match.
    """
    body = await request.json()

    # Validate auth token if configured
    if settings.gsi_auth_token:
        auth = body.get("auth", {})
        if auth.get("token") != settings.gsi_auth_token:
            return Response(status_code=401)

    # Parse and update state -- never fail the response
    try:
        gsi_state_manager.update(body)
    except Exception:
        logger.warning("Failed to parse GSI payload", exc_info=True)

    return Response(status_code=200)
