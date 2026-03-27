from dataclasses import asdict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from data.cache import data_cache

router = APIRouter()


class HeroResponse(BaseModel):
    """Pydantic response model for Hero data."""

    id: int
    name: str
    localized_name: str
    internal_name: str
    primary_attr: str | None = None
    attack_type: str | None = None
    roles: list | None = None
    base_health: float | None = None
    base_mana: float | None = None
    base_armor: float | None = None
    base_str: float | None = None
    base_agi: float | None = None
    base_int: float | None = None
    str_gain: float | None = None
    agi_gain: float | None = None
    int_gain: float | None = None
    base_attack_min: int | None = None
    base_attack_max: int | None = None
    attack_range: int | None = None
    move_speed: int | None = None
    img_url: str | None = None
    icon_url: str | None = None

    model_config = {"from_attributes": True}


@router.get("/heroes", response_model=list[HeroResponse])
async def list_heroes():
    """Return all heroes ordered by localized name (from cache)."""
    return [asdict(h) for h in data_cache.get_all_heroes()]


@router.get("/heroes/{hero_id}", response_model=HeroResponse)
async def get_hero(hero_id: int):
    """Return a single hero by ID (from cache)."""
    hero = data_cache.get_hero(hero_id)
    if hero is None:
        raise HTTPException(status_code=404, detail="Hero not found")
    return asdict(hero)
