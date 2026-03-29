"""POST /api/suggest-hero endpoint.

Returns a ranked list of hero candidates for the user's role, filtered by
HERO_ROLE_VIABLE viability and scored by synergy/counter matrices from DataCache.
"""
import logging
from fastapi import APIRouter
from data.cache import data_cache
from engine.schemas import SuggestHeroRequest, SuggestHeroResponse
from engine.hero_selector import HeroSelector

logger = logging.getLogger(__name__)
router = APIRouter()

_selector = HeroSelector()


@router.post("/suggest-hero", response_model=SuggestHeroResponse)
async def suggest_hero(request: SuggestHeroRequest) -> SuggestHeroResponse:
    """Return ranked hero suggestions for the given role and draft context.

    Filters heroes to those viable for the requested position (HERO_ROLE_VIABLE),
    scores each candidate using synergy/counter matrices from DataCache, and
    returns top N ranked by composite score descending.

    When matrices are placeholder/absent, scores are all 0.0 and
    matrices_available=False is set in the response.
    """
    logger.info(
        "SuggestHero request: role=%d allies=%s enemies=%s excluded=%s",
        request.role, request.ally_ids, request.enemy_ids, request.excluded_hero_ids,
    )
    response = _selector.get_suggestions(request, data_cache)
    logger.info(
        "SuggestHero response: %d suggestions, matrices_available=%s",
        len(response.suggestions), response.matrices_available,
    )
    return response
