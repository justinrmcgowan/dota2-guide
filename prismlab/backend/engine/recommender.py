"""Hybrid recommendation orchestrator.

Coordinates the rules engine (deterministic, instant) and LLM engine (Claude API,
structured output) into a unified recommendation pipeline with merge, deduplication,
fallback, and item ID validation. Includes response caching for cost efficiency.
"""

import hashlib
import time
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from engine.schemas import (
    RecommendRequest,
    RecommendResponse,
    RecommendPhase,
    ItemRecommendation,
    RuleResult,
    LLMRecommendation,
)
from engine.rules import RulesEngine
from engine.llm import LLMEngine, FallbackReason
from engine.context_builder import ContextBuilder
from data.models import Item

logger = logging.getLogger(__name__)


class ResponseCache:
    """In-memory response cache with TTL. Hash request -> cached response."""

    def __init__(self, ttl_seconds: float = 300.0) -> None:
        self.ttl = ttl_seconds
        self._cache: dict[str, tuple[RecommendResponse, float]] = {}

    def _hash_request(self, request: RecommendRequest) -> str:
        payload = request.model_dump_json(exclude_none=True)
        return hashlib.sha256(payload.encode()).hexdigest()

    def get(self, request: RecommendRequest) -> RecommendResponse | None:
        key = self._hash_request(request)
        entry = self._cache.get(key)
        if entry is None:
            return None
        response, timestamp = entry
        if time.monotonic() - timestamp > self.ttl:
            del self._cache[key]
            return None
        return response

    def set(self, request: RecommendRequest, response: RecommendResponse) -> None:
        key = self._hash_request(request)
        self._cache[key] = (response, time.monotonic())

    def cleanup(self) -> None:
        """Evict expired entries."""
        now = time.monotonic()
        expired = [k for k, (_, ts) in self._cache.items() if now - ts > self.ttl]
        for k in expired:
            del self._cache[k]


class HybridRecommender:
    """Orchestrates rules -> LLM -> merge -> validate pipeline.

    Rules fire first (instant, deterministic). Claude API fires second
    (structured output, 10s timeout). Results are merged with rules taking
    priority. If LLM fails, falls back to rules-only.
    """

    def __init__(
        self,
        rules: RulesEngine,
        llm: LLMEngine,
        context_builder: ContextBuilder,
        response_cache: ResponseCache | None = None,
    ):
        self.rules = rules
        self.llm = llm
        self.context_builder = context_builder
        self.response_cache = response_cache

    # Reason-specific fallback messages for the overall_strategy field
    FALLBACK_STRATEGIES = {
        FallbackReason.timeout: "AI timed out -- showing rules-based build. Try again in a moment.",
        FallbackReason.parse_error: "AI response was malformed -- showing rules-based build.",
        FallbackReason.api_error: "AI service unavailable -- showing rules-based build. Try again shortly.",
        FallbackReason.rate_limited: "AI rate limited -- showing rules-based build. Try again in a moment.",
    }

    async def recommend(
        self, request: RecommendRequest, db: AsyncSession
    ) -> RecommendResponse:
        """Run full hybrid recommendation pipeline.

        0. Check response cache (return immediately on hit)
        1. Rules engine fires instantly (deterministic)
        2. Context builder assembles Claude prompt
        3. Claude API generates structured recommendations
        4. Merge rules + LLM results (rules take priority, deduplicate)
        5. Validate all item_ids against DB
        6. Return response with metadata (fallback, fallback_reason, model, latency_ms)
        7. Cache the response for future identical requests
        """
        # Step 0: Check cache
        if self.response_cache:
            cached = self.response_cache.get(request)
            if cached is not None:
                logger.info("Returning cached response for request")
                return cached

        start = time.monotonic()

        # Step 1: Rules fire instantly (deterministic, no API call)
        rules_items = self.rules.evaluate(request)
        logger.info("Rules engine produced %d recommendations", len(rules_items))

        # Step 2: Build Claude prompt context
        user_message = await self.context_builder.build(request, rules_items, db)

        # Step 3: Call Claude with timeout + fallback
        llm_result: LLMRecommendation | None = None
        fallback = False
        fallback_reason: FallbackReason | None = None

        llm_result, fallback_reason = await self.llm.generate(user_message)

        if llm_result is None:
            fallback = True
            if fallback_reason is None:
                fallback_reason = FallbackReason.api_error

        # Step 4: Merge results
        if llm_result and not fallback:
            phases = self._merge(rules_items, llm_result)
            overall_strategy = llm_result.overall_strategy
            neutral_items = llm_result.neutral_items
        else:
            phases = self._rules_only(rules_items)
            overall_strategy = self.FALLBACK_STRATEGIES.get(
                fallback_reason,
                "Rules-based recommendations only. AI reasoning unavailable.",
            )
            neutral_items = []

        # Step 5: Filter purchased items (if any)
        if request.purchased_items:
            phases = self._filter_purchased(phases, request.purchased_items)

        # Step 6: Validate all item_ids against DB
        phases = await self._validate_item_ids(phases, db)

        elapsed_ms = int((time.monotonic() - start) * 1000)
        response = RecommendResponse(
            phases=phases,
            overall_strategy=overall_strategy,
            neutral_items=neutral_items,
            fallback=fallback,
            fallback_reason=fallback_reason.value if fallback_reason else None,
            model=LLMEngine.MODEL if not fallback else None,
            latency_ms=elapsed_ms,
        )

        # Step 7: Cache the response
        if self.response_cache:
            self.response_cache.set(request, response)

        return response

    def _merge(
        self, rules_items: list[RuleResult], llm_result: LLMRecommendation
    ) -> list[RecommendPhase]:
        """Merge rules results into LLM phases. Rules take priority.

        - Start with LLM phases as the base
        - For each RuleResult, find matching phase by name
        - If phase exists, prepend rule item (rules take priority)
        - If phase doesn't exist, create a new RecommendPhase
        - Deduplicate: if rule item_id already in LLM phase, remove LLM duplicate
        """
        # Build a mutable dict of phase_name -> RecommendPhase
        phase_map: dict[str, RecommendPhase] = {}
        phase_order: list[str] = []

        for phase in llm_result.phases:
            phase_map[phase.phase] = phase.model_copy(deep=True)
            phase_order.append(phase.phase)

        for rule in rules_items:
            rule_item = ItemRecommendation(
                item_id=rule.item_id,
                item_name=rule.item_name,
                reasoning=rule.reasoning,
                priority=rule.priority,
                conditions=None,
            )

            if rule.phase in phase_map:
                existing_phase = phase_map[rule.phase]
                # Remove LLM duplicate if same item_id
                existing_phase.items = [
                    item
                    for item in existing_phase.items
                    if item.item_id != rule.item_id
                ]
                # Prepend rule item (rules take priority)
                existing_phase.items.insert(0, rule_item)
            else:
                # Create a new phase for this rule
                new_phase = RecommendPhase(
                    phase=rule.phase,
                    items=[rule_item],
                )
                phase_map[rule.phase] = new_phase
                phase_order.append(rule.phase)

        return [phase_map[name] for name in phase_order]

    def _rules_only(self, rules_items: list[RuleResult]) -> list[RecommendPhase]:
        """Group RuleResults by phase and convert to RecommendPhase objects.

        Used as fallback when LLM is unavailable.
        """
        phase_groups: dict[str, list[ItemRecommendation]] = {}
        phase_order: list[str] = []

        for rule in rules_items:
            item = ItemRecommendation(
                item_id=rule.item_id,
                item_name=rule.item_name,
                reasoning=rule.reasoning,
                priority=rule.priority,
                conditions=None,
            )
            if rule.phase not in phase_groups:
                phase_groups[rule.phase] = []
                phase_order.append(rule.phase)
            phase_groups[rule.phase].append(item)

        return [
            RecommendPhase(phase=phase_name, items=items)
            for phase_name, items in [(name, phase_groups[name]) for name in phase_order]
        ]

    def _filter_purchased(
        self, phases: list[RecommendPhase], purchased: list[int]
    ) -> list[RecommendPhase]:
        """Remove already-purchased items from recommendations.

        Filters out items whose item_id appears in the purchased set.
        Removes phases that become empty after filtering.
        """
        purchased_set = set(purchased)
        filtered_phases: list[RecommendPhase] = []
        for phase in phases:
            remaining = [
                item for item in phase.items if item.item_id not in purchased_set
            ]
            if remaining:
                filtered_phases.append(
                    RecommendPhase(
                        phase=phase.phase,
                        items=remaining,
                        timing=phase.timing,
                        gold_budget=phase.gold_budget,
                    )
                )
        return filtered_phases

    async def _validate_item_ids(
        self, phases: list[RecommendPhase], db: AsyncSession
    ) -> list[RecommendPhase]:
        """Validate all item_ids against the Item table. Filter out invalid ones.

        Logs a warning for each filtered-out item. Removes empty phases.
        """
        result = await db.execute(select(Item.id, Item.cost, Item.internal_name))
        item_info: dict[int, tuple[int | None, str]] = {
            row[0]: (row[1], row[2]) for row in result.fetchall()
        }

        validated_phases: list[RecommendPhase] = []
        for phase in phases:
            valid_items: list[ItemRecommendation] = []
            for item in phase.items:
                if item.item_id in item_info:
                    cost, slug = item_info[item.item_id]
                    valid_items.append(
                        item.model_copy(update={
                            "gold_cost": cost,
                            "item_name": slug,
                        })
                    )
                else:
                    logger.warning(
                        "Filtered invalid item_id %d (%s) from recommendations",
                        item.item_id,
                        item.item_name,
                    )
            if valid_items:
                validated_phases.append(
                    RecommendPhase(
                        phase=phase.phase,
                        items=valid_items,
                        timing=phase.timing,
                        gold_budget=phase.gold_budget,
                    )
                )

        return validated_phases
