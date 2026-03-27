"""Auto-seed logic for populating the database from OpenDota API on first startup."""

import logging

from sqlalchemy import select, func

from data.database import async_session
from data.models import Hero, Item, HeroAbilityData
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

            # Fallback: neutral items have empty hints but abilities with descriptions
            if active_desc is None and info.get("tier") is not None:
                abilities = info.get("abilities")
                if isinstance(abilities, list) and len(abilities) > 0:
                    desc = abilities[0].get("description") if isinstance(abilities[0], dict) else None
                    if desc:
                        active_desc = desc

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
                is_neutral=info.get("qual") == "rare" or (info.get("tier") is not None and not info.get("cost")),
                tier=info.get("tier"),
                bonuses=bonuses,
                active_desc=active_desc,
                passive_desc=info.get("lore"),
                img_url=f"{STEAM_CDN_BASE}/items/{internal_name}.png",
            )
            session.add(item)
            item_count_seeded += 1

        # Seed ability data (D-03: loaded at startup)
        try:
            abilities_data = await client.fetch_abilities()
            hero_abilities_data = await client.fetch_hero_abilities()

            # Build internal_name -> id from just-seeded heroes
            hero_internal_to_id: dict[str, int] = {}
            for _hid_str, info in heroes_data.items():
                hero_internal_to_id[info["name"]] = info["id"]

            ability_count = 0
            for hero_internal_name, hero_ab_info in hero_abilities_data.items():
                hero_id = hero_internal_to_id.get(hero_internal_name)
                if hero_id is None:
                    continue

                raw_abilities = hero_ab_info.get("abilities", [])
                filtered = [
                    a for a in raw_abilities
                    if isinstance(a, str)
                    and not a.startswith("generic_")
                    and not a.startswith("special_bonus_")
                    and a in abilities_data
                ]

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

                session.add(HeroAbilityData(
                    hero_id=hero_id,
                    abilities_json=hero_ability_dict,
                ))
                ability_count += 1

            logger.info("Seeded ability data for %d heroes.", ability_count)

        except Exception as e:
            logger.warning("Ability data seeding failed (non-fatal): %s", str(e))

        await session.commit()
        print(f"Seeded {hero_count_seeded} heroes, {item_count_seeded} items, and ability data.")
        logger.info("Seeded %d heroes, %d items, and ability data.", hero_count_seeded, item_count_seeded)
