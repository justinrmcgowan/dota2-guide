"""POST /api/recommend endpoint.

Exposes the hybrid recommendation pipeline via a single endpoint.
Accepts draft context (hero, role, playstyle, side, lane, opponents)
and returns phased item recommendations with reasoning.

Rate-limited per IP (10s cooldown). Responses cached for 5min (configurable).
"""

import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from data.database import get_db
from data.opendota_client import OpenDotaClient
from data.cache import data_cache
from engine.schemas import RecommendRequest, RecommendResponse
from engine.rules import RulesEngine
from engine.llm import LLMEngine
from engine.ollama_engine import OllamaEngine
from engine.cost_tracker import CostTracker
from engine.context_builder import ContextBuilder
from engine.exemplar_matcher import ExemplarMatcher
from engine.recommender import HybridRecommender, HierarchicalCache
from middleware.rate_limiter import check_rate_limit
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Singleton instances (created once, reused across requests)
_opendota = OpenDotaClient(api_key=settings.opendota_api_key)
_rules = RulesEngine(cache=data_cache)
_llm = LLMEngine()
_ollama = OllamaEngine()
_cost_tracker = CostTracker()
_exemplar_matcher = ExemplarMatcher()
_context_builder = ContextBuilder(
    opendota_client=_opendota, cache=data_cache,
    exemplar_matcher=_exemplar_matcher,
)
_response_cache = HierarchicalCache(l1_ttl=3600.0, l2_ttl=300.0, l3_ttl=300.0)
_recommender = HybridRecommender(
    rules=_rules, llm=_llm, context_builder=_context_builder,
    response_cache=_response_cache, cache=data_cache,
    ollama=_ollama, cost_tracker=_cost_tracker,
)


@router.post("/recommend", response_model=RecommendResponse)
async def recommend(
    request: RecommendRequest,
    db: AsyncSession = Depends(get_db),
    _rate_limit: None = Depends(check_rate_limit),
):
    """Generate item recommendations for a Dota 2 draft context.

    Runs the hybrid engine: rules first (instant), then Claude API (structured output),
    merges results, validates item IDs, and returns phased timeline with reasoning.

    Falls back to rules-only if Claude API fails or times out (10s hard timeout).
    Response includes fallback flag, model name, and latency_ms metadata.
    """
    logger.info(
        "Recommend request: hero=%d role=%d opponents=%s",
        request.hero_id, request.role, request.lane_opponents,
    )
    response = await _recommender.recommend(request, db)
    logger.info(
        "Recommend response: %d phases, fallback=%s, latency=%dms",
        len(response.phases), response.fallback, response.latency_ms or 0,
    )
    return response
