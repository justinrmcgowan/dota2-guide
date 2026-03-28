"""Live match API route: fetch current draft for a player.

Tries Stratz GraphQL first (primary, faster, broader coverage), then falls
back to OpenDota /live endpoint. Returns a normalized LiveMatchResponse with
all 10 players regardless of data source.
"""

import logging

from fastapi import APIRouter
from pydantic import BaseModel

from config import settings
from data.stratz_client import StratzClient
from data.opendota_client import OpenDotaClient

logger = logging.getLogger(__name__)

router = APIRouter()

# Instantiate clients at module level -- reused across requests
_stratz: StratzClient | None = (
    StratzClient(settings.stratz_api_token) if settings.stratz_api_token else None
)
_opendota = OpenDotaClient(settings.opendota_api_key)


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class LiveMatchPlayer(BaseModel):
    """A single player in a live match."""

    account_id: int
    hero_id: int
    is_radiant: bool
    player_slot: int
    position: int | None = None  # 1-5 from Stratz, None from OpenDota


class LiveMatchResponse(BaseModel):
    """Normalized live match data returned to the frontend."""

    match_id: int
    game_state: str  # HERO_SELECTION, STRATEGY_TIME, PRE_GAME, GAME_IN_PROGRESS, etc.
    game_time: int
    players: list[LiveMatchPlayer]
    source: str  # "stratz" or "opendota"
    radiant_score: int = 0
    dire_score: int = 0


# ---------------------------------------------------------------------------
# Stratz position enum -> integer mapping
# ---------------------------------------------------------------------------

_STRATZ_POSITION_MAP: dict[str, int] = {
    "POSITION_1": 1,
    "POSITION_2": 2,
    "POSITION_3": 3,
    "POSITION_4": 4,
    "POSITION_5": 5,
}


# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------


def _normalize_stratz(raw: dict) -> LiveMatchResponse:
    """Convert Stratz live match response to LiveMatchResponse."""
    players = []
    for p in raw.get("players", []):
        position_str = p.get("position")
        position = _STRATZ_POSITION_MAP.get(position_str) if position_str else None
        players.append(
            LiveMatchPlayer(
                account_id=p.get("steamAccountId", 0),
                hero_id=p.get("heroId", 0),
                is_radiant=p.get("isRadiant", False),
                player_slot=p.get("playerSlot", 0),
                position=position,
            )
        )

    return LiveMatchResponse(
        match_id=raw.get("matchId", 0),
        game_state=raw.get("gameState", "UNKNOWN"),
        game_time=raw.get("gameTime", 0),
        players=players,
        source="stratz",
        radiant_score=raw.get("radiantScore", 0),
        dire_score=raw.get("direScore", 0),
    )


def _normalize_opendota(raw: dict) -> LiveMatchResponse:
    """Convert OpenDota /live game response to LiveMatchResponse."""
    players = []
    for p in raw.get("players", []):
        # OpenDota: team=0 is Radiant, team=1 is Dire
        team = p.get("team", 0)
        players.append(
            LiveMatchPlayer(
                account_id=p.get("account_id", 0),
                hero_id=p.get("hero_id", 0),
                is_radiant=(team == 0),
                player_slot=p.get("team_slot", 0),
                position=None,  # OpenDota team_slot is connection order, NOT role
            )
        )

    # OpenDota match_id comes as a string
    match_id_raw = raw.get("match_id", 0)
    match_id = int(match_id_raw) if match_id_raw else 0

    return LiveMatchResponse(
        match_id=match_id,
        game_state="GAME_IN_PROGRESS",  # OpenDota /live doesn't provide game state
        game_time=raw.get("game_time", 0),
        players=players,
        source="opendota",
        radiant_score=raw.get("radiant_score", 0),
        dire_score=raw.get("dire_score", 0),
    )


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.get("/live-match/{account_id}", response_model=LiveMatchResponse | None)
async def get_live_match(account_id: int) -> LiveMatchResponse | None:
    """Fetch current live match for a player.

    Tries Stratz GraphQL first (primary). If Stratz is not configured, fails,
    or returns no match, falls back to OpenDota /live endpoint.

    Args:
        account_id: Player's 32-bit Steam account ID.

    Returns:
        Normalized live match data with all players, or null if no live match found.
    """
    # Try Stratz first (primary source per D-01)
    if _stratz is not None:
        try:
            stratz_result = await _stratz.fetch_live_match_for_player(account_id)
            if stratz_result is not None:
                return _normalize_stratz(stratz_result)
        except Exception:
            logger.exception("Stratz fetch failed for account %d, trying OpenDota", account_id)

    # Fallback: OpenDota /live
    try:
        opendota_result = await _opendota.fetch_live_match_for_player(account_id)
        if opendota_result is not None:
            return _normalize_opendota(opendota_result)
    except Exception:
        logger.exception("OpenDota live fetch also failed for account %d", account_id)

    logger.debug("No live match found for account %d from any source", account_id)
    return None
