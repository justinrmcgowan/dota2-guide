"""POST /api/parse-screenshot endpoint.

Receives a base64-encoded scoreboard screenshot, sends it to Claude Vision
for structured extraction, fuzzy-matches extracted names against the DB,
and returns validated results with per-item confidence levels.
"""

import logging
import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from data.database import get_db
from data.models import Hero, Item
from engine.llm import LLMEngine
from engine.schemas import (
    ScreenshotParseRequest,
    ScreenshotParseResponse,
    ParsedHero,
    ParsedItem,
)
from engine.name_matcher import match_hero_name, match_item_name, resolve_confidence

logger = logging.getLogger(__name__)
router = APIRouter()

_VALID_MEDIA_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}

# Singleton LLMEngine (reuses the same AsyncAnthropic client)
_llm = LLMEngine()


@router.post("/parse-screenshot", response_model=ScreenshotParseResponse)
async def parse_screenshot(
    req: ScreenshotParseRequest,
    db: AsyncSession = Depends(get_db),
) -> ScreenshotParseResponse:
    """Parse a Dota 2 scoreboard screenshot via Claude Vision.

    Accepts base64-encoded image data, calls Claude Vision for structured
    extraction, fuzzy-matches hero and item names against the database,
    and returns parsed results with confidence levels.
    """
    start = time.time()

    # Validate media type
    if req.media_type not in _VALID_MEDIA_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid media_type '{req.media_type}'. Must be one of: {', '.join(sorted(_VALID_MEDIA_TYPES))}",
        )

    # Load all heroes and items from DB for prompt anchoring and post-processing
    heroes = (await db.execute(select(Hero))).scalars().all()
    items = (await db.execute(select(Item))).scalars().all()

    hero_names = [h.localized_name for h in heroes]
    item_names = [i.name for i in items if i.name]

    # Call Claude Vision
    vision_result = await _llm.parse_screenshot(
        image_base64=req.image_base64,
        media_type=req.media_type,
        hero_names=hero_names,
        item_names=item_names,
    )

    latency_ms = int((time.time() - start) * 1000)

    if vision_result is None:
        logger.warning("Vision API call failed or timed out")
        return ScreenshotParseResponse(
            error="parse_failed",
            message="Vision API call failed or timed out",
            latency_ms=latency_ms,
        )

    if vision_result.error is not None:
        logger.info("Vision returned error: %s", vision_result.error)
        return ScreenshotParseResponse(
            error=vision_result.error,
            message=vision_result.message,
            latency_ms=latency_ms,
        )

    # Post-process each VisionHero: fuzzy-match names against DB
    parsed_heroes: list[ParsedHero] = []

    for vh in vision_result.heroes:
        hero_obj, hero_ratio = match_hero_name(vh.hero_name, heroes)

        matched_items: list[ParsedItem] = []
        for vi in vh.items:
            item_obj, item_ratio = match_item_name(vi.name, items)
            if item_obj is not None:
                matched_items.append(
                    ParsedItem(
                        display_name=item_obj.name,
                        internal_name=item_obj.internal_name,
                        confidence=resolve_confidence(vi.confidence, item_ratio),
                    )
                )
            # If item_obj is None (below threshold), skip this item

        parsed_heroes.append(
            ParsedHero(
                hero_name=hero_obj.localized_name if hero_obj else vh.hero_name,
                hero_id=hero_obj.id if hero_obj else None,
                internal_name=hero_obj.internal_name if hero_obj else None,
                team=vh.team,
                items=matched_items,
                kills=vh.kills,
                deaths=vh.deaths,
                assists=vh.assists,
                level=vh.level,
            )
        )

    logger.info(
        "Screenshot parsed: %d heroes, latency=%dms",
        len(parsed_heroes),
        latency_ms,
    )

    return ScreenshotParseResponse(
        heroes=parsed_heroes,
        latency_ms=latency_ms,
    )
