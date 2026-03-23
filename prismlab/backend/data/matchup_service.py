"""Matchup data fetch/cache pipeline.

Fetches hero-vs-hero win rates and item popularity from OpenDota,
caches in SQLite MatchupData table. Returns stale data without blocking
on refresh. Deduplicates concurrent fetches per matchup pair.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from data.models import MatchupData, Item
from data.opendota_client import OpenDotaClient

logger = logging.getLogger(__name__)

STALE_THRESHOLD = timedelta(hours=24)

# In-memory locks to deduplicate concurrent fetches per matchup pair.
# Key format: "{hero_id}_{opponent_id}"
_fetch_locks: dict[str, asyncio.Lock] = {}


async def get_or_fetch_matchup(
    hero_id: int,
    opponent_id: int,
    db: AsyncSession,
    client: OpenDotaClient,
) -> MatchupData | None:
    """Get matchup data from cache, fetch from OpenDota if missing or stale.

    Never blocks on freshness -- returns stale data immediately and
    schedules background refresh if needed. Only blocks on the first
    fetch when no cached data exists.
    """
    try:
        result = await db.execute(
            select(MatchupData).where(
                MatchupData.hero_id == hero_id,
                MatchupData.opponent_id == opponent_id,
            )
        )
        cached = result.scalar_one_or_none()

        if cached:
            # Check staleness
            if cached.updated_at:
                age = datetime.now(timezone.utc) - cached.updated_at.replace(
                    tzinfo=timezone.utc
                )
                if age > STALE_THRESHOLD:
                    # Return stale data immediately, refresh in background
                    asyncio.create_task(
                        _refresh_matchup(hero_id, opponent_id, db, client)
                    )
            return cached

        # No cache -- first request must wait
        return await _refresh_matchup(hero_id, opponent_id, db, client)

    except Exception:
        logger.exception(
            "Error in get_or_fetch_matchup(hero=%d, opponent=%d)",
            hero_id,
            opponent_id,
        )
        return None


async def _refresh_matchup(
    hero_id: int,
    opponent_id: int,
    db: AsyncSession,
    client: OpenDotaClient,
) -> MatchupData | None:
    """Fetch fresh matchup data from OpenDota API.

    Uses per-pair locking to deduplicate concurrent fetches.
    """
    lock_key = f"{hero_id}_{opponent_id}"
    if lock_key not in _fetch_locks:
        _fetch_locks[lock_key] = asyncio.Lock()

    async with _fetch_locks[lock_key]:
        try:
            matchups = await client.fetch_hero_matchups(hero_id)

            opponent_data = next(
                (m for m in matchups if m["hero_id"] == opponent_id),
                None,
            )
            if not opponent_data:
                return None

            games = opponent_data["games_played"]
            win_rate = (
                opponent_data["wins"] / games if games > 0 else 0.5
            )

            matchup = MatchupData(
                hero_id=hero_id,
                opponent_id=opponent_id,
                win_rate=win_rate,
                games_played=games,
                bracket="high",
                updated_at=datetime.now(timezone.utc),
            )
            await db.merge(matchup)
            await db.commit()
            return matchup

        except Exception:
            logger.exception(
                "Failed to refresh matchup data (hero=%d, opponent=%d)",
                hero_id,
                opponent_id,
            )
            return None


async def get_hero_item_popularity(
    hero_id: int,
    db: AsyncSession,
    client: OpenDotaClient,
) -> dict | None:
    """Fetch item popularity for a hero from OpenDota.

    Returns the raw dict with start_game_items, early_game_items,
    mid_game_items, late_game_items keys. Each maps item_id -> count.
    """
    try:
        return await client.fetch_hero_item_popularity(hero_id)
    except Exception:
        logger.exception(
            "Failed to fetch item popularity for hero %d", hero_id
        )
        return None


async def get_neutral_items_by_tier(
    db: AsyncSession,
) -> dict[int, list[dict]]:
    """Get all neutral items grouped by tier number.

    Returns dict mapping tier (1-5) to list of item dicts.
    Each dict has keys: id, name, internal_name, active_desc.
    Tiers with no items are absent from the result.
    """
    result = await db.execute(
        select(Item).where(
            Item.is_neutral == True,  # noqa: E712
            Item.tier.isnot(None),
        )
    )
    all_neutrals = result.scalars().all()

    grouped: dict[int, list[dict]] = {}
    for item in all_neutrals:
        tier = item.tier
        if tier not in grouped:
            grouped[tier] = []
        grouped[tier].append({
            "id": item.id,
            "name": item.name,
            "internal_name": item.internal_name,
            "active_desc": item.active_desc or "",
        })

    return grouped


async def get_relevant_items(
    hero_id: int,
    role: int,
    db: AsyncSession,
) -> list[dict]:
    """Filter item catalog to ~40-50 items relevant to this hero/role.

    Excludes: recipes, neutral items, zero-cost items.
    Applies role budget: max 10000g for cores (Pos 1-3), 5500g for supports (Pos 4-5).
    Returns list of {"id", "name", "cost"} dicts sorted by cost, capped at 50.
    """
    result = await db.execute(
        select(Item).where(
            Item.is_recipe == False,  # noqa: E712
            Item.is_neutral == False,  # noqa: E712
            Item.cost > 0,
        )
    )
    all_items = result.scalars().all()

    max_cost = 10000 if role <= 3 else 5500
    filtered = [
        {"id": item.id, "name": item.name, "cost": item.cost}
        for item in all_items
        if item.cost and item.cost <= max_cost
    ]

    filtered.sort(key=lambda x: x["cost"])
    return filtered[:50]
