"""Hybrid recommendation orchestrator.

Coordinates the rules engine (deterministic, instant) and LLM engine (Claude API,
structured output) into a unified recommendation pipeline with merge, deduplication,
fallback, and item ID validation. Includes response caching for cost efficiency.

Item validation uses DataCache -- zero DB queries for item lookups on the hot path.
"""

import hashlib
import time
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from engine.schemas import (
    RecommendRequest,
    RecommendResponse,
    RecommendPhase,
    ItemRecommendation,
    ItemTimingResponse,
    ComponentStep,
    BuildPathResponse,
    RuleResult,
    LLMRecommendation,
)
from engine.rules import RulesEngine
from engine.llm import LLMEngine, FallbackReason
from engine.context_builder import ContextBuilder
from engine.timing_zones import classify_timing_zones
from data.cache import DataCache

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

    def clear(self) -> None:
        """Clear all cached responses (e.g., after data pipeline refresh)."""
        self._cache.clear()


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
        cache: DataCache | None = None,
    ):
        self.rules = rules
        self.llm = llm
        self.context_builder = context_builder
        self.response_cache = response_cache
        self.cache = cache

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

        # Step 6: Validate all item_ids against cache (zero DB queries)
        phases = self._validate_item_ids(phases)

        # Step 6b: Enrich with timing data (zero DB queries, uses DataCache)
        timing_data: list[ItemTimingResponse] = []
        if self.cache:
            timing_data = self._enrich_timing_data(request.hero_id, phases)

        # Step 6c: Enrich with build path data (zero DB queries, uses DataCache)
        build_paths: list[BuildPathResponse] = []
        if self.cache:
            build_paths = self._enrich_build_paths(request, phases)

        elapsed_ms = int((time.monotonic() - start) * 1000)
        response = RecommendResponse(
            phases=phases,
            overall_strategy=overall_strategy,
            neutral_items=neutral_items,
            timing_data=timing_data,
            build_paths=build_paths,
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

    def _validate_item_ids(
        self, phases: list[RecommendPhase]
    ) -> list[RecommendPhase]:
        """Validate all item_ids against cached item data. Filter out invalid ones.

        Logs a warning for each filtered-out item. Removes empty phases.
        """
        item_info = self.cache.get_item_validation_map() if self.cache else {}

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

    def _enrich_timing_data(
        self, hero_id: int, phases: list[RecommendPhase]
    ) -> list[ItemTimingResponse]:
        """Build timing response data for all recommended items.

        Looks up timing benchmarks from DataCache, classifies zones,
        and returns pre-computed display data for the frontend.
        Zero DB queries -- all data from in-memory cache.
        """
        timings = self.cache.get_hero_timings(hero_id)
        if not timings:
            return []

        # Collect all recommended item internal_names from validated phases
        recommended_items: set[str] = set()
        for phase in phases:
            for item in phase.items:
                recommended_items.add(item.item_name)

        results: list[ItemTimingResponse] = []
        for item_name in recommended_items:
            buckets = timings.get(item_name)
            if not buckets:
                continue
            classified = classify_timing_zones(buckets)
            if classified is None:
                continue
            results.append(ItemTimingResponse(
                item_name=item_name,
                buckets=classified["buckets_classified"],
                is_urgent=classified["is_urgent"],
                good_range=classified["good_range"],
                ontrack_range=classified["ontrack_range"],
                late_range=classified["late_range"],
                good_win_rate=classified["good_win_rate"],
                late_win_rate=classified["late_win_rate"],
                confidence=classified["confidence"],
                total_games=classified["total_games"],
            ))
        return results

    def _enrich_build_paths(
        self,
        request: RecommendRequest,
        phases: list[RecommendPhase],
    ) -> list[BuildPathResponse]:
        """Build component ordering for all recommended items.

        Reads ItemCached.components from DataCache (zero DB queries).
        Uses Claude's component_order if present and valid against actual components;
        falls back to heuristic ordering based on lane_result.
        Only generates build paths for items with >= 2 components.
        """
        if not self.cache:
            return []

        results: list[BuildPathResponse] = []
        for phase in phases:
            for item in phase.items:
                cached_item = self.cache.get_item(item.item_id)
                if not cached_item or not cached_item.components or len(cached_item.components) < 2:
                    continue

                # Determine component order: Claude's ordering takes priority
                component_names = list(cached_item.components)
                if item.component_order:
                    # Validate Claude's ordering: keep only names that match actual components
                    actual_set = set(component_names)
                    valid_order = [n for n in item.component_order if n in actual_set]
                    # Append any components Claude omitted (preserve completeness)
                    for name in component_names:
                        if name not in valid_order:
                            valid_order.append(name)
                    component_names = valid_order
                elif request.lane_result == "lost":
                    # Heuristic: defensive components first when losing lane
                    component_names = self._sort_defensive_first(component_names)

                # Build steps with costs from cache
                steps: list[ComponentStep] = []
                for i, comp_name in enumerate(component_names, start=1):
                    comp_id = self.cache.item_name_to_id(comp_name)
                    comp_item = self.cache.get_item(comp_id) if comp_id else None
                    steps.append(ComponentStep(
                        item_name=comp_name,
                        item_id=comp_id if comp_id is not None else 0,
                        cost=comp_item.cost if comp_item else None,
                        reason="",  # filled below from build_path_notes or heuristic
                        position=i,
                    ))

                # Use Claude's build_path_notes as the overall ordering justification
                notes = item.build_path_notes or ""

                results.append(BuildPathResponse(
                    item_name=item.item_name,
                    steps=steps,
                    build_path_notes=notes,
                ))

        return results

    def _sort_defensive_first(self, component_names: list[str]) -> list[str]:
        """Heuristic: sort components with highest HP/armor/magic resist value first.

        Uses a keyword-based proxy against internal_names. Defensive components
        (hood, ring_of_health, platemail, vit_booster, crown, belt_of_strength)
        are sorted before offensive/utility components.
        Preserves relative order within each group.
        """
        DEFENSIVE_KEYWORDS = {
            "ring_of_health", "vit_booster", "platemail", "hood_of_defiance",
            "cloak", "belt_of_strength", "crown", "bracer",
            "helm_of_iron_will", "ring_of_regen", "chain_mail",
        }
        defensive = [n for n in component_names if n in DEFENSIVE_KEYWORDS]
        offensive = [n for n in component_names if n not in DEFENSIVE_KEYWORDS]
        return defensive + offensive
