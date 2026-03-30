"""Automated data refresh pipeline for keeping hero/item data current from OpenDota."""

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select

from data.database import async_session
from data.models import Hero, Item, DataRefreshLog, HeroAbilityData
from data.opendota_client import OpenDotaClient
from config import settings

logger = logging.getLogger(__name__)

STEAM_CDN_BASE = "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react"


async def refresh_all_data() -> DataRefreshLog:
    """Main refresh pipeline: fetch heroes and items from OpenDota and upsert into DB.

    Creates its own async session (runs outside request context from scheduler).
    Logs a DataRefreshLog entry tracking the result.
    """
    started_at = datetime.now(timezone.utc)
    logger.info("Starting data refresh pipeline...")

    async with async_session() as session:
        try:
            client = OpenDotaClient(api_key=settings.opendota_api_key)

            # Refresh heroes
            heroes_data = await client.fetch_heroes()
            hero_count = 0
            for _hero_id_str, info in heroes_data.items():
                slug = info["name"].replace("npc_dota_hero_", "")
                hero = Hero(
                    id=info["id"],
                    name=info["localized_name"],
                    localized_name=info["localized_name"],
                    internal_name=info["name"],
                    primary_attr=info.get("primary_attr", "all"),
                    attack_type=info.get("attack_type", "Melee"),
                    roles=info.get("roles", []),
                    base_health=info.get("base_health", 200),
                    base_mana=info.get("base_mana", 75),
                    base_armor=info.get("base_armor", 0),
                    base_str=info.get("base_str", 0),
                    base_agi=info.get("base_agi", 0),
                    base_int=info.get("base_int", 0),
                    str_gain=info.get("str_gain", 0),
                    agi_gain=info.get("agi_gain", 0),
                    int_gain=info.get("int_gain", 0),
                    base_attack_min=info.get("base_attack_min", 0),
                    base_attack_max=info.get("base_attack_max", 0),
                    attack_range=info.get("attack_range", 150),
                    move_speed=info.get("move_speed", 300),
                    img_url=f"{STEAM_CDN_BASE}/heroes/{slug}.png",
                    icon_url=f"{STEAM_CDN_BASE}/heroes/icons/{slug}.png",
                    updated_at=datetime.now(timezone.utc),
                )
                await session.merge(hero)
                hero_count += 1

            # Refresh items
            items_data = await client.fetch_items()
            item_count = 0
            for internal_name, info in items_data.items():
                if "id" not in info:
                    continue

                hint = info.get("hint")
                active_desc = None
                if isinstance(hint, list) and len(hint) > 0:
                    active_desc = hint[0]
                elif isinstance(hint, str):
                    active_desc = hint

                attrib = info.get("attrib")
                bonuses = None
                if isinstance(attrib, list) and len(attrib) > 0:
                    bonuses = {
                        a.get("key", f"attr_{i}"): a.get("value")
                        for i, a in enumerate(attrib)
                        if isinstance(a, dict)
                    }

                item = Item(
                    id=info["id"],
                    name=info.get("dname", internal_name),
                    internal_name=internal_name,
                    cost=info.get("cost"),
                    components=info.get("components"),
                    is_recipe=internal_name.startswith("recipe_"),
                    is_neutral=info.get("qual") == "rare" and not info.get("cost"),
                    tier=info.get("tier"),
                    bonuses=bonuses,
                    active_desc=active_desc,
                    passive_desc=info.get("lore"),
                    img_url=f"{STEAM_CDN_BASE}/items/{internal_name}.png",
                    updated_at=datetime.now(timezone.utc),
                )
                await session.merge(item)
                item_count += 1

            # Refresh ability constants (D-03: daily alongside heroes/items)
            try:
                abilities_data = await client.fetch_abilities()
                hero_abilities_data = await client.fetch_hero_abilities()

                # Build hero internal_name -> id lookup from just-fetched heroes
                hero_internal_to_id: dict[str, int] = {}
                for _hid_str, hinfo in heroes_data.items():
                    hero_internal_to_id[hinfo["name"]] = hinfo["id"]

                ability_count = 0
                for hero_internal_name, hero_ab_info in hero_abilities_data.items():
                    hero_id = hero_internal_to_id.get(hero_internal_name)
                    if hero_id is None:
                        continue

                    raw_abilities = hero_ab_info.get("abilities", [])
                    # Filter out generic_hidden, talent entries, and non-string values (Pitfall 6)
                    filtered = [
                        a for a in raw_abilities
                        if isinstance(a, str)
                        and not a.startswith("generic_")
                        and not a.startswith("special_bonus_")
                        and a in abilities_data
                    ]

                    # Build ability dict for this hero
                    hero_ability_dict: dict = {}
                    for ability_key in filtered:
                        ab_data = abilities_data[ability_key]
                        hero_ability_dict[ability_key] = {
                            "dname": ab_data.get("dname", ability_key),
                            "behavior": ab_data.get("behavior", ""),
                            "dmg_type": ab_data.get("dmg_type"),
                            "bkbpierce": ab_data.get("bkbpierce"),
                            "dispellable": ab_data.get("dispellable"),
                        }

                    record = HeroAbilityData(
                        hero_id=hero_id,
                        abilities_json=hero_ability_dict,
                        updated_at=datetime.now(timezone.utc),
                    )
                    await session.merge(record)
                    ability_count += 1

                logger.info("Refreshed ability data for %d heroes.", ability_count)

            except Exception as e:
                logger.warning("Ability data refresh failed (non-fatal): %s", str(e))
                # Non-fatal: ability data is supplementary. Heroes/items still refreshed.

            # Refresh pro baselines (Divine+ item popularity per hero)
            try:
                from data.cache import data_cache

                # Build item name lookup from just-fetched items data
                item_name_lookup: dict[int, str] = {}
                for _iname, iinfo in items_data.items():
                    if "id" in iinfo:
                        item_name_lookup[iinfo["id"]] = iinfo.get("dname", _iname)

                baselines: dict[int, dict] = {}
                for _hid_str, hinfo in heroes_data.items():
                    hid = hinfo["id"]
                    raw = await client.fetch_hero_item_popularity_by_bracket(hid)
                    if raw:
                        parsed = _parse_item_baselines(raw, item_name_lookup)
                        if parsed:
                            baselines[hid] = parsed
                    await asyncio.sleep(0.1)  # Rate limit: 10 req/s for OpenDota
                data_cache.set_hero_item_baselines(baselines)
                logger.info("Refreshed pro baselines for %d heroes.", len(baselines))
            except Exception as e:
                logger.warning("Pro baselines refresh failed (non-fatal): %s", str(e))

            await session.commit()

            # Log success
            completed_at = datetime.now(timezone.utc)
            log_entry = DataRefreshLog(
                refresh_type="full",
                status="success",
                heroes_updated=hero_count,
                items_updated=item_count,
                started_at=started_at,
                completed_at=completed_at,
            )
            session.add(log_entry)
            await session.commit()

            # Coordinated three-layer cache invalidation:
            # 1. DataCache refreshes first (new data) -- uses fresh session (INT-05)
            # 2. RulesEngine sees new data automatically via DataCache reference
            # 3. ResponseCache clears (stale responses built from old data) (INT-06)
            from data.cache import data_cache
            async with async_session() as fresh_session:
                await data_cache.refresh(fresh_session)
            logger.info(
                "DataCache refreshed: %d heroes, %d items",
                len(data_cache._heroes), len(data_cache._items),
            )

            from api.routes.recommend import _response_cache
            _response_cache.clear()
            logger.info("ResponseCache cleared after data refresh.")

            logger.info(
                "Data refresh completed: %d heroes, %d items, ability data refreshed.",
                hero_count, item_count,
            )
            return log_entry

        except Exception as e:
            logger.error("Data refresh failed: %s", str(e))
            completed_at = datetime.now(timezone.utc)
            log_entry = DataRefreshLog(
                refresh_type="full",
                status="failed",
                heroes_updated=0,
                items_updated=0,
                error_message=str(e),
                started_at=started_at,
                completed_at=completed_at,
            )
            # Use a fresh session for error logging in case the original is borked
            async with async_session() as err_session:
                err_session.add(log_entry)
                await err_session.commit()
            raise


_BASELINE_PHASE_MAP = {
    "start_game_items": "starting",
    "early_game_items": "laning",
    "mid_game_items": "core",
    "late_game_items": "late_game",
}


def _parse_item_baselines(
    raw: dict, item_names: dict[int, str]
) -> dict[str, list[tuple[int, str, int, float]]]:
    """Parse raw OpenDota itemPopularity response into structured baselines.

    Args:
        raw: OpenDota response with start_game_items, early_game_items, etc.
        item_names: {item_id: display_name} lookup from items data.

    Returns:
        {phase_label: [(item_id, item_name, count, win_rate), ...]}
        where items are sorted by count descending, top 5 per phase.
        win_rate is 0.0 (OpenDota itemPopularity only provides counts).
    """
    result: dict[str, list[tuple[int, str, int, float]]] = {}
    for api_key, phase_label in _BASELINE_PHASE_MAP.items():
        phase_data = raw.get(api_key, {})
        if not phase_data:
            continue

        items: list[tuple[int, str, int, float]] = []
        for item_id_str, count in phase_data.items():
            item_id = int(item_id_str)
            name = item_names.get(item_id, f"Item #{item_id}")
            items.append((item_id, name, int(count), 0.0))

        # Sort by count descending, take top 5
        items.sort(key=lambda x: x[2], reverse=True)
        result[phase_label] = items[:5]

    return result


async def get_last_refresh() -> DataRefreshLog | None:
    """Query the most recent successful refresh log entry.

    Returns None if no successful refresh has been recorded yet.
    """
    async with async_session() as session:
        result = await session.execute(
            select(DataRefreshLog)
            .where(DataRefreshLog.status == "success")
            .order_by(DataRefreshLog.completed_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
