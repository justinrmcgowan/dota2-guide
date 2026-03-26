import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from data.database import Base, get_db
from data.models import Hero, Item
from main import app


test_engine = create_async_engine(
    "sqlite+aiosqlite://",
    connect_args={"check_same_thread": False},
)
test_async_session = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def test_db_setup():
    """Create tables and seed test data."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with test_async_session() as session:
        # Seed test heroes
        heroes = [
            Hero(
                id=1,
                name="Anti-Mage",
                localized_name="Anti-Mage",
                internal_name="npc_dota_hero_antimage",
                primary_attr="agi",
                attack_type="Melee",
                roles=["Carry", "Escape"],
            ),
            Hero(
                id=2,
                name="Axe",
                localized_name="Axe",
                internal_name="npc_dota_hero_axe",
                primary_attr="str",
                attack_type="Melee",
                roles=["Initiator", "Durable"],
            ),
            Hero(
                id=3,
                name="Crystal Maiden",
                localized_name="Crystal Maiden",
                internal_name="npc_dota_hero_crystal_maiden",
                primary_attr="int",
                attack_type="Ranged",
                roles=["Support", "Nuker"],
            ),
        ]
        session.add_all(heroes)

        # Additional heroes used by rules engine tests
        extra_heroes = [
            Hero(
                id=22, name="Zeus", localized_name="Zeus",
                internal_name="npc_dota_hero_zuus",
                primary_attr="int", attack_type="Ranged",
                roles=["Nuker", "Carry"],
            ),
            Hero(
                id=69, name="Bristleback", localized_name="Bristleback",
                internal_name="npc_dota_hero_bristleback",
                primary_attr="str", attack_type="Melee",
                roles=["Carry", "Durable"],
            ),
            Hero(
                id=12, name="Phantom Assassin", localized_name="Phantom Assassin",
                internal_name="npc_dota_hero_phantom_assassin",
                primary_attr="agi", attack_type="Melee",
                roles=["Carry", "Escape"],
            ),
            Hero(
                id=32, name="Riki", localized_name="Riki",
                internal_name="npc_dota_hero_riki",
                primary_attr="agi", attack_type="Melee",
                roles=["Carry", "Escape"],
            ),
            Hero(
                id=57, name="Lifestealer", localized_name="Lifestealer",
                internal_name="npc_dota_hero_life_stealer",
                primary_attr="str", attack_type="Melee",
                roles=["Carry", "Durable"],
            ),
            Hero(
                id=33, name="Enigma", localized_name="Enigma",
                internal_name="npc_dota_hero_enigma",
                primary_attr="int", attack_type="Ranged",
                roles=["Initiator", "Jungler"],
            ),
            Hero(
                id=97, name="Magnus", localized_name="Magnus",
                internal_name="npc_dota_hero_magnataur",
                primary_attr="str", attack_type="Melee",
                roles=["Initiator", "Disabler"],
            ),
            Hero(
                id=26, name="Lion", localized_name="Lion",
                internal_name="npc_dota_hero_lion",
                primary_attr="int", attack_type="Ranged",
                roles=["Support", "Disabler"],
            ),
            Hero(
                id=40, name="Venomancer", localized_name="Venomancer",
                internal_name="npc_dota_hero_venomancer",
                primary_attr="agi", attack_type="Ranged",
                roles=["Support", "Nuker"],
            ),
            Hero(
                id=84, name="Ogre Magi", localized_name="Ogre Magi",
                internal_name="npc_dota_hero_ogre_magi",
                primary_attr="str", attack_type="Melee",
                roles=["Support", "Nuker"],
            ),
            Hero(
                id=110, name="Skywrath Mage", localized_name="Skywrath Mage",
                internal_name="npc_dota_hero_skywrath_mage",
                primary_attr="int", attack_type="Ranged",
                roles=["Support", "Nuker"],
            ),
            Hero(
                id=47, name="Faceless Void", localized_name="Faceless Void",
                internal_name="npc_dota_hero_faceless_void",
                primary_attr="agi", attack_type="Melee",
                roles=["Carry", "Initiator"],
            ),
            Hero(
                id=93, name="Slark", localized_name="Slark",
                internal_name="npc_dota_hero_slark",
                primary_attr="agi", attack_type="Melee",
                roles=["Carry", "Escape"],
            ),
            Hero(
                id=72, name="Alchemist", localized_name="Alchemist",
                internal_name="npc_dota_hero_alchemist",
                primary_attr="str", attack_type="Melee",
                roles=["Carry", "Durable"],
            ),
            Hero(
                id=67, name="Clinkz", localized_name="Clinkz",
                internal_name="npc_dota_hero_clinkz",
                primary_attr="agi", attack_type="Ranged",
                roles=["Carry", "Escape"],
            ),
            Hero(
                id=94, name="Weaver", localized_name="Weaver",
                internal_name="npc_dota_hero_weaver",
                primary_attr="agi", attack_type="Ranged",
                roles=["Carry", "Escape"],
            ),
            Hero(
                id=11, name="Sven", localized_name="Sven",
                internal_name="npc_dota_hero_sven",
                primary_attr="str", attack_type="Melee",
                roles=["Carry", "Disabler"],
            ),
            Hero(
                id=44, name="Phantom Lancer", localized_name="Phantom Lancer",
                internal_name="npc_dota_hero_phantom_lancer",
                primary_attr="agi", attack_type="Melee",
                roles=["Carry", "Escape"],
            ),
            Hero(
                id=18, name="Juggernaut", localized_name="Juggernaut",
                internal_name="npc_dota_hero_juggernaut",
                primary_attr="agi", attack_type="Melee",
                roles=["Carry"],
            ),
            Hero(
                id=91, name="Wraith King", localized_name="Wraith King",
                internal_name="npc_dota_hero_skeleton_king",
                primary_attr="str", attack_type="Melee",
                roles=["Carry", "Durable"],
            ),
            Hero(
                id=120, name="Huskar", localized_name="Huskar",
                internal_name="npc_dota_hero_huskar",
                primary_attr="str", attack_type="Ranged",
                roles=["Carry", "Durable"],
            ),
            Hero(
                id=103, name="Necrophos", localized_name="Necrophos",
                internal_name="npc_dota_hero_necrolyte",
                primary_attr="int", attack_type="Ranged",
                roles=["Nuker", "Durable"],
            ),
        ]
        session.add_all(extra_heroes)

        # Seed test items (extended for rules engine coverage)
        items = [
            Item(id=1, name="Blink Dagger", internal_name="blink", cost=2250),
            Item(id=2, name="Black King Bar", internal_name="black_king_bar", cost=4050),
            Item(id=29, name="Quelling Blade", internal_name="quelling_blade", cost=100),
            Item(id=36, name="Magic Stick", internal_name="magic_stick", cost=200),
            Item(id=40, name="Dust of Appearance", internal_name="dust", cost=80),
            Item(id=43, name="Sentry Ward", internal_name="ward_sentry", cost=50),
            Item(id=48, name="Power Treads", internal_name="power_treads", cost=1400),
            Item(id=50, name="Phase Boots", internal_name="phase_boots", cost=1500),
            Item(id=99, name="Soul Ring", internal_name="soul_ring", cost=805),
            Item(id=102, name="Force Staff", internal_name="force_staff", cost=2200),
            Item(id=116, name="Black King Bar", internal_name="bkb", cost=4050),
            Item(id=119, name="Shiva's Guard", internal_name="shivas_guard", cost=4750),
            Item(id=180, name="Arcane Boots", internal_name="arcane_boots", cost=1300),
            Item(id=225, name="Monkey King Bar", internal_name="monkey_king_bar", cost=4975),
            Item(id=235, name="Assault Cuirass", internal_name="assault", cost=5250),
            Item(id=249, name="Silver Edge", internal_name="silver_edge", cost=5450),
            Item(id=271, name="Spirit Vessel", internal_name="spirit_vessel", cost=2980),
            # Recipe and neutral items for filter testing
            Item(id=300, name="Recipe: Assault Cuirass", internal_name="recipe_assault",
                 cost=1300, is_recipe=True),
            Item(id=301, name="Mysterious Hat", internal_name="mysterious_hat",
                 cost=0, is_neutral=True, tier=1,
                 active_desc="Grants +1 mana regeneration"),
            Item(id=350, name="Chipped Vest", internal_name="chipped_vest",
                 cost=0, is_neutral=True, tier=1,
                 active_desc="Returns 28 damage when attacked"),
            Item(id=351, name="Psychic Headband", internal_name="psychic_headband",
                 cost=0, is_neutral=True, tier=3,
                 active_desc="Pushes the target 400 units away"),
            Item(id=352, name="Spider Legs", internal_name="spider_legs",
                 cost=0, is_neutral=True, tier=5,
                 active_desc="Grants free pathing and 25% move speed"),
            # Items for new rules (Phase 14)
            Item(id=56, name="Infused Raindrops", internal_name="infused_raindrop", cost=225),
            Item(id=187, name="Mekansm", internal_name="mekansm", cost=1775),
            Item(id=231, name="Pipe of Insight", internal_name="pipe", cost=3475),
            Item(id=190, name="Orchid Malevolence", internal_name="orchid", cost=3475),
            Item(id=168, name="Heaven's Halberd", internal_name="heavens_halberd", cost=3550),
            Item(id=185, name="Ghost Scepter", internal_name="ghost", cost=1500),
            # Expensive item to test budget filtering
            Item(id=302, name="Divine Rapier", internal_name="rapier", cost=5950),
        ]
        session.add_all(items)

        await session.commit()

    yield

    # Drop all tables for isolation
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def test_client(test_db_setup):
    """Create an async test client with database dependency override."""

    async def override_get_db():
        async with test_async_session() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_db_session(test_db_setup):
    """Yield a raw async session for unit tests that need DB access but not HTTP."""
    async with test_async_session() as session:
        yield session
