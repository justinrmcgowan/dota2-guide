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

        # Seed test items
        items = [
            Item(id=1, name="Blink Dagger", internal_name="blink", cost=2250),
            Item(id=2, name="Black King Bar", internal_name="black_king_bar", cost=4050),
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
