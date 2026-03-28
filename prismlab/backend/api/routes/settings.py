"""Settings API routes: GSI config, engine mode, and budget endpoints.

Provides endpoints for GSI configuration file generation, engine mode
status, and monthly API budget tracking (Phase 26).
"""

from fastapi import APIRouter, Response

from config import settings
from api.routes.recommend import _cost_tracker

router = APIRouter()

# Valve VDF format -- NOT JSON. Double braces for Python .format() escaping.
GSI_CONFIG_TEMPLATE = '''"gamestate_integration_prismlab"
{{
    "uri"               "http://{host}:{port}/gsi"
    "timeout"           "5.0"
    "buffer"            "0.1"
    "throttle"          "0.5"
    "heartbeat"         "30.0"
    "data"
    {{
        "provider"      "1"
        "map"           "1"
        "player"        "1"
        "hero"          "1"
        "abilities"     "1"
        "items"         "1"
        "buildings"     "1"
    }}
    "auth"
    {{
        "token"         "{token}"
    }}
}}
'''


@router.get("/settings/defaults")
async def get_settings_defaults():
    """Return default settings for the frontend.

    The frontend fetches this on first load to pre-fill the Steam ID
    input if localStorage is empty. Per D-10, the STEAM_ID env var
    provides a default for single-user deployments.
    """
    return {"steam_id": settings.steam_id}


@router.get("/gsi-config")
async def get_gsi_config(host: str, port: int = 8421) -> Response:
    """Generate and return a Dota 2 GSI config file for download.

    The file is a VDF (Valve Data Format) config that tells Dota 2
    where to send game state updates.
    """
    config_content = GSI_CONFIG_TEMPLATE.format(
        host=host,
        port=port,
        token=settings.gsi_auth_token,
    )
    return Response(
        content=config_content,
        media_type="text/plain",
        headers={
            "Content-Disposition": 'attachment; filename="gamestate_integration_prismlab.cfg"'
        },
    )


@router.get("/settings/engine")
async def get_engine_settings():
    """Return current engine mode and budget summary.

    Used by the frontend Settings panel to display mode selector
    and budget status (Phase 26: D-10, D-11).
    """
    return {
        "mode": settings.recommendation_mode,
        "budget_monthly": settings.api_budget_monthly,
        "budget_used": _cost_tracker.get_usage(),
    }


@router.get("/settings/budget")
async def get_budget_status():
    """Return current month's API budget usage.

    Detailed budget endpoint: month, cost, requests, budget cap,
    exceeded flag, warning flag. Used by frontend budget display.
    """
    return _cost_tracker.get_usage()
