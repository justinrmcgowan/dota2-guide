"""Settings API routes: GSI config file generator.

Provides an endpoint to download a Dota 2 GSI configuration file with
the user's IP address and auth token pre-filled.
"""

from fastapi import APIRouter, Response

from config import settings

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
