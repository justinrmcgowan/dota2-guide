"""Admin and data freshness endpoints for Prismlab."""

from fastapi import APIRouter, BackgroundTasks
from sqlalchemy import select

from data.refresh import refresh_all_data, get_last_refresh
from data.database import async_session
from data.models import Hero

router = APIRouter()


@router.post("/admin/refresh-data")
async def trigger_refresh(background_tasks: BackgroundTasks):
    """Trigger a manual data refresh from OpenDota API.

    Runs the refresh pipeline in the background so the endpoint returns immediately.
    """
    background_tasks.add_task(refresh_all_data)
    return {"status": "started", "message": "Data refresh initiated"}


@router.get("/api/data-freshness")
async def get_data_freshness():
    """Return the timestamp of the last successful data refresh.

    Falls back to Hero.updated_at if no refresh log exists (initial seed scenario).
    """
    last_refresh = await get_last_refresh()

    if last_refresh:
        return {
            "last_refresh": last_refresh.completed_at.isoformat() if last_refresh.completed_at else None,
            "heroes_updated": last_refresh.heroes_updated,
            "items_updated": last_refresh.items_updated,
        }

    # Fallback: check Hero.updated_at from any hero (covers initial seed)
    async with async_session() as session:
        result = await session.execute(
            select(Hero.updated_at).limit(1)
        )
        hero_updated = result.scalar_one_or_none()

    return {
        "last_refresh": hero_updated.isoformat() if hero_updated else None,
        "heroes_updated": 0,
        "items_updated": 0,
    }
