"""Automated data refresh pipeline for keeping hero/item data current from OpenDota."""

import logging
from datetime import datetime, timezone

from sqlalchemy import select

from data.database import async_session
from data.models import Hero, Item, DataRefreshLog
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
                    is_neutral=info.get("qual") == "rare",
                    tier=info.get("tier"),
                    bonuses=bonuses,
                    active_desc=active_desc,
                    passive_desc=info.get("lore"),
                    img_url=f"{STEAM_CDN_BASE}/items/{internal_name}.png",
                    updated_at=datetime.now(timezone.utc),
                )
                await session.merge(item)
                item_count += 1

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

            logger.info(
                "Data refresh completed: %d heroes, %d items updated.",
                hero_count,
                item_count,
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
