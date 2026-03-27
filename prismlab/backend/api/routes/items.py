from dataclasses import asdict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from data.cache import data_cache

router = APIRouter()


class ItemResponse(BaseModel):
    """Pydantic response model for Item data."""

    id: int
    name: str
    internal_name: str
    cost: int | None = None
    components: list | None = None
    is_recipe: bool = False
    is_neutral: bool = False
    tier: int | None = None
    bonuses: dict | None = None
    active_desc: str | None = None
    passive_desc: str | None = None
    category: str | None = None
    tags: list | None = None
    img_url: str | None = None

    model_config = {"from_attributes": True}


@router.get("/items", response_model=list[ItemResponse])
async def list_items():
    """Return all items ordered by name (from cache)."""
    return [asdict(i) for i in data_cache.get_all_items()]


@router.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int):
    """Return a single item by ID (from cache)."""
    item = data_cache.get_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return asdict(item)
