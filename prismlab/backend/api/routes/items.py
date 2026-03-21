from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from data.database import get_db
from data.models import Item

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
async def list_items(db: AsyncSession = Depends(get_db)):
    """Return all items ordered by name."""
    result = await db.execute(select(Item).order_by(Item.name))
    return result.scalars().all()


@router.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int, db: AsyncSession = Depends(get_db)):
    """Return a single item by ID."""
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
