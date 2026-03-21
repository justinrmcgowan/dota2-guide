"""Auto-seed logic for populating the database from OpenDota API on first startup."""

import logging

from sqlalchemy import select, func

from data.database import async_session
from data.models import Hero, Item
from data.opendota_client import OpenDotaClient
from config import settings

logger = logging.getLogger(__name__)

STEAM_CDN_BASE = "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react"


async def seed_if_empty():
    """Seed the database with hero and item data if tables are empty.

    Called during FastAPI lifespan startup. Skips seeding if heroes already exist.
    Fetches data from OpenDota /constants/heroes and /constants/items endpoints.
    """
    async with async_session() as session:
        hero_count = await session.scalar(select(func.count()).select_from(Hero))
        if hero_count and hero_count > 0:
            logger.info("Database already seeded (%d heroes). Skipping.", hero_count)
            return

        logger.info("Database is empty. Seeding from OpenDota API...")
        client = OpenDotaClient(api_key=settings.opendota_api_key)

        # Seed heroes
        heroes_data = await client.fetch_heroes()
        hero_count_seeded = 0
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
            )
            session.add(hero)
            hero_count_seeded += 1

        # Seed items
        items_data = await client.fetch_items()
        item_count_seeded = 0
        for internal_name, info in items_data.items():
            # Skip entries with no "id" field (malformed data)
            if "id" not in info:
                continue

            # Extract active description from hint (may be a list)
            hint = info.get("hint")
            active_desc = None
            if isinstance(hint, list) and len(hint) > 0:
                active_desc = hint[0]
            elif isinstance(hint, str):
                active_desc = hint

            # Extract bonuses from attrib
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
            )
            session.add(item)
            item_count_seeded += 1

        await session.commit()
        print(f"Seeded {hero_count_seeded} heroes and {item_count_seeded} items.")
        logger.info("Seeded %d heroes and %d items.", hero_count_seeded, item_count_seeded)
