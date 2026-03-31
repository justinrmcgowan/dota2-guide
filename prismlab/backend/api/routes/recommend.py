"""POST /api/recommend endpoint.

Exposes the hybrid recommendation pipeline via a single endpoint.
Accepts draft context (hero, role, playstyle, side, lane, opponents)
and returns phased item recommendations with reasoning.

Rate-limited per IP (10s cooldown). Responses cached for 5min (configurable).
"""

import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
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
from engine.recommender import HybridRecommender, ResponseCache
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
_response_cache = ResponseCache(ttl_seconds=settings.response_cache_ttl_seconds)
_recommender = HybridRecommender(
    rules=_rules, llm=_llm, context_builder=_context_builder,
    response_cache=_response_cache, cache=data_cache,
    ollama=_ollama, cost_tracker=_cost_tracker,
)


@router.post("/recommend/stream")
async def recommend_stream(
    request: RecommendRequest,
    db: AsyncSession = Depends(get_db),
    _rate_limit: None = Depends(check_rate_limit),
):
    """SSE streaming recommendation endpoint.

    Returns Server-Sent Events:
    - event: rules -- immediate rules-only items
    - event: phases -- full LLM recommendation
    - event: enrichment -- timing, build paths, win condition
    - event: done -- stream complete
    """
    logger.info("Stream recommend: hero=%d role=%d", request.hero_id, request.role)

    # Check hierarchical cache first -- if hit, return full response as single event
    if _response_cache:
        cached = _response_cache.get(request)
        if cached is not None:
            async def cached_stream():
                yield f"event: phases\ndata: {cached.model_dump_json()}\n\n"
                yield f"event: done\ndata: {{}}\n\n"
            return StreamingResponse(
                cached_stream(),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
            )

    return StreamingResponse(
        _recommender.recommend_stream(request, db),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
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
