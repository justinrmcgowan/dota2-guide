"""Matchup and timing data fetch/cache pipeline.

Fetches hero-vs-hero win rates, item popularity, and item timing benchmarks
from OpenDota. Caches in SQLite tables. Returns stale data without blocking
on refresh. Deduplicates concurrent fetches per matchup pair / per hero.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from data.models import MatchupData, Item, ItemTimingData
from data.cache import TimingBucket
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


async def get_or_fetch_hero_timings(
    hero_id: int,
    db: AsyncSession,
    client: OpenDotaClient,
) -> dict[str, list[TimingBucket]] | None:
    """Get timing benchmarks for a hero. Stale-while-revalidate pattern (D-01).

    Returns dict of {item_name: [TimingBucket, ...]} from DataCache.
    If not in cache/DB, fetches from OpenDota and populates both.
    Only fetches heroes that are actually queried -- no batch crawl.
    """
    from data.cache import data_cache

    try:
        # 1. Check DataCache first (zero DB, instant)
        cached = data_cache.get_hero_timings(hero_id)
        if cached is not None:
            # Check DB staleness for background refresh
            result = await db.execute(
                select(ItemTimingData).where(ItemTimingData.hero_id == hero_id)
            )
            db_row = result.scalar_one_or_none()
            if db_row and db_row.updated_at:
                age = datetime.now(timezone.utc) - db_row.updated_at.replace(
                    tzinfo=timezone.utc
                )
                if age > STALE_THRESHOLD:
                    asyncio.create_task(
                        _refresh_hero_timings(hero_id, db, client)
                    )
            return cached

        # 2. Check DB (cache might be empty after restart but DB has data)
        result = await db.execute(
            select(ItemTimingData).where(ItemTimingData.hero_id == hero_id)
        )
        db_row = result.scalar_one_or_none()

        if db_row and db_row.timings_json:
            # Parse into cache and return
            timings = _parse_timings_json(db_row.timings_json)
            data_cache.set_hero_timings(hero_id, timings)

            # Check staleness for background refresh
            if db_row.updated_at:
                age = datetime.now(timezone.utc) - db_row.updated_at.replace(
                    tzinfo=timezone.utc
                )
                if age > STALE_THRESHOLD:
                    asyncio.create_task(
                        _refresh_hero_timings(hero_id, db, client)
                    )
            return timings

        # 3. No cache, no DB -- first request must wait
        return await _refresh_hero_timings(hero_id, db, client)

    except Exception:
        logger.exception(
            "Error in get_or_fetch_hero_timings(hero=%d)", hero_id
        )
        return None


def _parse_timings_json(
    timings_json: dict[str, list[dict]],
) -> dict[str, list[TimingBucket]]:
    """Parse raw timings JSON blob into typed TimingBucket dicts.

    Handles games/wins string-to-int conversion (Pitfall 1) and
    confidence classification (D-07: strong >= 1000, moderate >= 200, weak < 200).
    """
    result: dict[str, list[TimingBucket]] = {}
    for item_name, buckets_raw in timings_json.items():
        buckets = []
        for bucket in buckets_raw:
            games = int(bucket["games"])
            wins = int(bucket["wins"])
            confidence = (
                "strong" if games >= 1000
                else "moderate" if games >= 200
                else "weak"
            )
            buckets.append(TimingBucket(
                time=bucket["time"],
                games=games,
                wins=wins,
                confidence=confidence,
            ))
        result[item_name] = buckets
    return result


async def _refresh_hero_timings(
    hero_id: int,
    db: AsyncSession,
    client: OpenDotaClient,
) -> dict[str, list[TimingBucket]] | None:
    """Fetch fresh timing data from OpenDota and cache in DB + DataCache.

    Uses per-hero locking to deduplicate concurrent fetches.
    One API call returns all items for a hero.
    """
    from data.cache import data_cache

    lock_key = f"timing_{hero_id}"
    if lock_key not in _fetch_locks:
        _fetch_locks[lock_key] = asyncio.Lock()

    async with _fetch_locks[lock_key]:
        try:
            raw_rows = await client.fetch_item_timings(hero_id)
            if raw_rows is None:
                return None

            # Group by item name: {item: [{time, games, wins}, ...]}
            grouped: dict[str, list[dict]] = {}
            for row in raw_rows:
                item = row["item"]
                if item not in grouped:
                    grouped[item] = []
                grouped[item].append({
                    "time": row["time"],
                    "games": row["games"],  # Keep as string for DB storage
                    "wins": row["wins"],    # Keep as string for DB storage
                })

            # Store in DB (one row per hero with all items)
            record = ItemTimingData(
                hero_id=hero_id,
                timings_json=grouped,
                updated_at=datetime.now(timezone.utc),
            )
            await db.merge(record)
            await db.commit()

            # Parse and update DataCache
            timings = _parse_timings_json(grouped)
            data_cache.set_hero_timings(hero_id, timings)

            logger.info(
                "Refreshed timing data for hero %d: %d items",
                hero_id, len(timings),
            )
            return timings

        except Exception:
            logger.exception(
                "Failed to refresh timing data for hero %d", hero_id
            )
            return None
