"""Hybrid recommendation orchestrator with 3-mode routing.

Coordinates the rules engine (deterministic, instant), Ollama (local LLM),
and Claude API (cloud LLM) into a unified recommendation pipeline with
merge, deduplication, fallback, and item ID validation.

Modes:
  - Fast: Rules-only, no LLM call (<1s target)
  - Auto: Ollama primary, Claude fallback on failure/escalation (<5s target)
  - Deep: Always Claude API with full reasoning (<15s target)

Item validation uses DataCache -- zero DB queries for item lookups on the hot path.
"""

from __future__ import annotations

import asyncio
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
    WinConditionResponse,
    RuleResult,
    LLMRecommendation,
)
from engine.win_condition import classify_draft
from engine.win_predictor import WinPredictor
from engine.rules import RulesEngine
from engine.llm import LLMEngine, FallbackReason
from engine.context_builder import ContextBuilder
from engine.timing_zones import classify_timing_zones
from data.cache import DataCache
from data.matchup_service import get_or_fetch_hero_timings
from engine.response_validator import ResponseValidator
from config import settings

logger = logging.getLogger(__name__)

# Lazy imports to avoid circular / load-time issues
TYPE_CHECKING = False
if TYPE_CHECKING:
    from engine.ollama_engine import OllamaEngine
    from engine.cost_tracker import CostTracker


class HierarchicalCache:
    """3-tier in-memory response cache with TTL.

    Tiers:
      L1 -- hero+role+lane (broad, 1h TTL) -- covers starting/laning builds
      L2 -- hero+role+lane+sorted_opponents (matchup, 5min TTL)
      L3 -- exact request hash (precise, 5min TTL)

    get() falls through L3 -> L2 -> L1, returning the first hit.
    set() writes to all three tiers atomically.
    set_l1() writes directly to L1 for cache warming without a full request.
    """

    def __init__(
        self,
        l1_ttl: float = 3600.0,
        l2_ttl: float = 300.0,
        l3_ttl: float = 300.0,
    ) -> None:
        self.l1_ttl = l1_ttl
        self.l2_ttl = l2_ttl
        self.l3_ttl = l3_ttl
        self._l1: dict[str, tuple[RecommendResponse, float]] = {}
        self._l2: dict[str, tuple[RecommendResponse, float]] = {}
        self._l3: dict[str, tuple[RecommendResponse, float]] = {}

    # ------------------------------------------------------------------
    # Key builders
    # ------------------------------------------------------------------

    @staticmethod
    def _l1_key(hero_id: int, role: int, lane: str) -> str:
        raw = f"{hero_id}:{role}:{lane}"
        return hashlib.sha256(raw.encode()).hexdigest()

    @staticmethod
    def _l2_key(hero_id: int, role: int, lane: str, lane_opponents: list[int], all_opponents: list[int]) -> str:
        sorted_ids = sorted(set(lane_opponents + all_opponents))
        ids_str = ",".join(str(i) for i in sorted_ids)
        raw = f"{hero_id}:{role}:{lane}:{ids_str}"
        return hashlib.sha256(raw.encode()).hexdigest()

    @staticmethod
    def _l3_key(request: RecommendRequest) -> str:
        payload = request.model_dump_json(exclude_none=True)
        return hashlib.sha256(payload.encode()).hexdigest()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, request: RecommendRequest) -> RecommendResponse | None:
        """Check L3 -> L2 -> L1. Return first valid (non-expired) hit or None."""
        now = time.monotonic()

        # L3: exact match
        l3_key = self._l3_key(request)
        entry = self._l3.get(l3_key)
        if entry is not None:
            response, ts = entry
            if now - ts <= self.l3_ttl:
                return response
            del self._l3[l3_key]

        # L2: matchup-level
        l2_key = self._l2_key(
            request.hero_id, request.role, request.lane,
            request.lane_opponents, request.all_opponents,
        )
        entry = self._l2.get(l2_key)
        if entry is not None:
            response, ts = entry
            if now - ts <= self.l2_ttl:
                return response
            del self._l2[l2_key]

        # L1: hero+role+lane
        l1_key = self._l1_key(request.hero_id, request.role, request.lane)
        entry = self._l1.get(l1_key)
        if entry is not None:
            response, ts = entry
            if now - ts <= self.l1_ttl:
                return response
            del self._l1[l1_key]

        return None

    def set(self, request: RecommendRequest, response: RecommendResponse) -> None:
        """Write response to all three tiers."""
        now = time.monotonic()

        l3_key = self._l3_key(request)
        self._l3[l3_key] = (response, now)

        l2_key = self._l2_key(
            request.hero_id, request.role, request.lane,
            request.lane_opponents, request.all_opponents,
        )
        self._l2[l2_key] = (response, now)

        l1_key = self._l1_key(request.hero_id, request.role, request.lane)
        self._l1[l1_key] = (response, now)

    def set_l1(
        self,
        hero_id: int,
        role: int,
        lane: str,
        response: RecommendResponse,
    ) -> None:
        """Direct L1 write for cache warming (no full request needed)."""
        l1_key = self._l1_key(hero_id, role, lane)
        self._l1[l1_key] = (response, time.monotonic())

    def cleanup(self) -> None:
        """Evict expired entries from all three tiers."""
        now = time.monotonic()
        for store, ttl in [
            (self._l1, self.l1_ttl),
            (self._l2, self.l2_ttl),
            (self._l3, self.l3_ttl),
        ]:
            expired = [k for k, (_, ts) in store.items() if now - ts > ttl]
            for k in expired:
                del store[k]

    def clear(self) -> None:
        """Clear all cached responses (e.g., after data pipeline refresh)."""
        self._l1.clear()
        self._l2.clear()
        self._l3.clear()


class HybridRecommender:
    """Orchestrates rules -> LLM -> merge -> validate pipeline with 3-mode routing.

    Modes:
      Fast  -- rules-only, no LLM call, <1s
      Auto  -- Ollama primary, Claude fallback on failure or complexity escalation
      Deep  -- always Claude API, full reasoning
    """

    def __init__(
        self,
        rules: RulesEngine,
        llm: LLMEngine,
        context_builder: ContextBuilder,
        response_cache: HierarchicalCache | None = None,
        cache: DataCache | None = None,
        ollama: OllamaEngine | None = None,
        cost_tracker: CostTracker | None = None,
    ):
        self.rules = rules
        self.llm = llm
        self.context_builder = context_builder
        self.response_cache = response_cache
        self.cache = cache
        self.ollama = ollama
        self.cost_tracker = cost_tracker
        self.response_validator = ResponseValidator(cache) if cache else None

    # Reason-specific fallback messages for the overall_strategy field
    FALLBACK_STRATEGIES = {
        FallbackReason.timeout: "AI timed out -- showing rules-based build. Try again in a moment.",
        FallbackReason.parse_error: "AI response was malformed -- showing rules-based build.",
        FallbackReason.api_error: "AI service unavailable -- showing rules-based build. Try again shortly.",
        FallbackReason.rate_limited: "AI rate limited -- showing rules-based build. Try again in a moment.",
        FallbackReason.ollama_error: "Local AI unavailable -- showing rules-based build.",
        FallbackReason.budget_exceeded: "Monthly API budget reached -- showing rules-based build.",
    }

    # ------------------------------------------------------------------
    # Main entry point: route by mode
    # ------------------------------------------------------------------

    async def recommend(
        self, request: RecommendRequest, db: AsyncSession
    ) -> RecommendResponse:
        """Run recommendation pipeline, routing to the appropriate mode path.

        0. Check response cache (return immediately on hit)
        1. Determine mode (request override or settings default)
        2. Route to _fast_path / _auto_path / _deep_path
        3. Enrich (timing, build paths, win condition)
        4. Cache and return
        """
        # Step 0: Check cache
        if self.response_cache:
            cached = self.response_cache.get(request)
            if cached is not None:
                logger.info("Returning cached response for request")
                return cached

        # Step 1: Determine mode
        mode = request.mode or settings.recommendation_mode

        # Step 2: Route
        if mode == "fast":
            response = await self._fast_path(request, db)
        elif mode == "auto":
            response = await self._auto_path(request, db)
        else:
            response = await self._deep_path(request, db)

        # Step 3: Cache the response
        if self.response_cache:
            self.response_cache.set(request, response)

        return response

    # ------------------------------------------------------------------
    # Fast path: rules-only, no LLM call
    # ------------------------------------------------------------------

    async def _fast_path(
        self, request: RecommendRequest, db: AsyncSession
    ) -> RecommendResponse:
        """Rules-only recommendations. No LLM call. Target <1s."""
        start = time.monotonic()

        rules_items = self.rules.evaluate(request)
        logger.info("Fast path: rules produced %d items", len(rules_items))

        phases = self._rules_only(rules_items)
        phases = self._validate_item_ids(phases)
        phases = self._deduplicate_across_phases(phases)

        # Enrich with timing, build paths, win condition (same as other paths)
        timing_data, build_paths, win_condition, win_probability = await self._enrich_all(
            request, phases, db
        )
        if win_condition:
            phases = self._adjust_priorities_for_win_condition(phases, win_condition)

        elapsed_ms = int((time.monotonic() - start) * 1000)
        response = RecommendResponse(
            phases=phases,
            overall_strategy="Rules-based build (Fast mode -- no AI reasoning).",
            neutral_items=[],
            timing_data=timing_data,
            build_paths=build_paths,
            win_condition=win_condition,
            win_probability=win_probability,
            fallback=False,
            fallback_reason=None,
            model=None,
            latency_ms=elapsed_ms,
            engine_mode="fast",
        )
        self._attach_budget_info(response)
        return response

    # ------------------------------------------------------------------
    # Auto path: Ollama primary, Claude fallback on failure/escalation
    # ------------------------------------------------------------------

    async def _auto_path(
        self, request: RecommendRequest, db: AsyncSession
    ) -> RecommendResponse:
        """Smart routing: Ollama primary, Claude fallback. Target <5s."""
        start = time.monotonic()

        # Step 1: Rules fire instantly
        rules_items = self.rules.evaluate(request)
        logger.info("Auto path: rules produced %d items", len(rules_items))

        # Step 2: Check if we should escalate to Claude
        should_escalate = self._should_escalate(request, rules_items)
        # Budget is "ok" when no cost_tracker is configured (no cap) or cap not exceeded
        budget_ok = self.cost_tracker is None or not self.cost_tracker.budget_exceeded()

        # Step 3: If should escalate AND budget allows, use Claude directly
        if should_escalate and budget_ok:
            logger.info("Auto path: escalating to Claude (complex matchup)")
            return await self._deep_path(request, db, engine_mode_label="auto")

        # Step 4: Use Ollama (if available)
        llm_result: LLMRecommendation | None = None
        fallback_reason: FallbackReason | None = None
        model_used: str | None = None

        if self.ollama:
            user_message = await self.context_builder.build(request, rules_items, db)
            llm_result, fallback_reason = await self.ollama.generate(user_message)
            if llm_result:
                model_used = f"ollama:{self.ollama.model}"

        # Step 5: If Ollama not available or failed, and budget allows, try Claude
        if llm_result is None and budget_ok:
            logger.info("Auto path: Ollama %s, falling back to Claude",
                        "unavailable" if not self.ollama else "failed")
            return await self._deep_path(request, db, engine_mode_label="auto")

        # Step 6: If Ollama failed and Claude budget exceeded, use rules-only
        if llm_result is None:
            logger.info("Auto path: Ollama failed + budget exceeded, rules-only fallback")
            fr = fallback_reason or FallbackReason.ollama_error
            phases = self._rules_only(rules_items)
            phases = self._validate_item_ids(phases)
            phases = self._deduplicate_across_phases(phases)

            timing_data, build_paths, win_condition, win_probability = await self._enrich_all(
                request, phases, db
            )
            if win_condition:
                phases = self._adjust_priorities_for_win_condition(phases, win_condition)

            elapsed_ms = int((time.monotonic() - start) * 1000)
            response = RecommendResponse(
                phases=phases,
                overall_strategy=self.FALLBACK_STRATEGIES.get(
                    fr, "AI unavailable -- showing rules-based build."
                ),
                neutral_items=[],
                timing_data=timing_data,
                build_paths=build_paths,
                win_condition=win_condition,
                win_probability=win_probability,
                fallback=True,
                fallback_reason=fr.value,
                model=None,
                latency_ms=elapsed_ms,
                engine_mode="auto",
            )
            self._attach_budget_info(response)
            return response

        # Step 7: Ollama succeeded -- merge, validate, enrich
        phases = self._merge(rules_items, llm_result)
        overall_strategy = llm_result.overall_strategy
        neutral_items = llm_result.neutral_items
        phases = self._validate_item_ids(phases)
        phases = self._deduplicate_across_phases(phases)

        # Step 7b: Post-parse validation with retry (retry via Claude, not Ollama)
        if self.response_validator:
            # user_message was built in Step 4 when self.ollama is set
            retry_phases, retry_strategy, retry_neutrals = await self._validate_and_retry(
                phases, request, rules_items, db, user_message
            )
            if retry_strategy is not None:
                phases = retry_phases
                overall_strategy = retry_strategy
                neutral_items = retry_neutrals or []

        timing_data, build_paths, win_condition, win_probability = await self._enrich_all(
            request, phases, db
        )
        if win_condition:
            phases = self._adjust_priorities_for_win_condition(phases, win_condition)

        elapsed_ms = int((time.monotonic() - start) * 1000)
        response = RecommendResponse(
            phases=phases,
            overall_strategy=overall_strategy,
            neutral_items=neutral_items,
            timing_data=timing_data,
            build_paths=build_paths,
            win_condition=win_condition,
            win_probability=win_probability,
            fallback=False,
            fallback_reason=None,
            model=model_used,
            latency_ms=elapsed_ms,
            engine_mode="auto",
        )
        self._attach_budget_info(response)
        return response

    # ------------------------------------------------------------------
    # Deep path: always Claude API, full reasoning
    # ------------------------------------------------------------------

    async def _deep_path(
        self,
        request: RecommendRequest,
        db: AsyncSession,
        engine_mode_label: str = "deep",
    ) -> RecommendResponse:
        """Always call Claude API with full reasoning. Target <15s."""
        start = time.monotonic()

        # Step 1: Rules fire instantly
        rules_items = self.rules.evaluate(request)
        logger.info("Deep path: rules produced %d items", len(rules_items))

        # Step 2: Build context + call Claude
        user_message = await self.context_builder.build(request, rules_items, db)
        llm_result, fallback_reason = await self.llm.generate(user_message)

        # Step 3: Track cost if available
        if llm_result and self.cost_tracker and self.llm.last_usage:
            await self.cost_tracker.record_usage(
                self.llm.last_usage["input_tokens"],
                self.llm.last_usage["output_tokens"],
                db,
            )

        # Step 4: Merge or fallback
        fallback = llm_result is None
        if llm_result and not fallback:
            phases = self._merge(rules_items, llm_result)
            overall_strategy = llm_result.overall_strategy
            neutral_items = llm_result.neutral_items
        else:
            if fallback_reason is None:
                fallback_reason = FallbackReason.api_error
            phases = self._rules_only(rules_items)
            overall_strategy = self.FALLBACK_STRATEGIES.get(
                fallback_reason,
                "Rules-based recommendations only. AI reasoning unavailable.",
            )
            neutral_items = []

        # Step 5: Validate, deduplicate, and enrich
        phases = self._validate_item_ids(phases)
        phases = self._deduplicate_across_phases(phases)

        # Step 5b: Post-parse validation with retry
        if not fallback and self.response_validator:
            retry_phases, retry_strategy, retry_neutrals = await self._validate_and_retry(
                phases, request, rules_items, db, user_message
            )
            if retry_strategy is not None:
                phases = retry_phases
                overall_strategy = retry_strategy
                neutral_items = retry_neutrals or []

        timing_data, build_paths, win_condition, win_probability = await self._enrich_all(
            request, phases, db
        )
        if win_condition:
            phases = self._adjust_priorities_for_win_condition(phases, win_condition)

        elapsed_ms = int((time.monotonic() - start) * 1000)
        response = RecommendResponse(
            phases=phases,
            overall_strategy=overall_strategy,
            neutral_items=neutral_items,
            timing_data=timing_data,
            build_paths=build_paths,
            win_condition=win_condition,
            win_probability=win_probability,
            fallback=fallback,
            fallback_reason=fallback_reason.value if fallback_reason else None,
            model=LLMEngine.MODEL if not fallback else None,
            latency_ms=elapsed_ms,
            engine_mode=engine_mode_label,
        )
        self._attach_budget_info(response)
        return response

    # ------------------------------------------------------------------
    # Escalation logic for Auto mode
    # ------------------------------------------------------------------

    def _should_escalate(
        self, request: RecommendRequest, rules_items: list[RuleResult]
    ) -> bool:
        """Determine if Auto mode should escalate to Claude for this request.

        Escalate when:
        - Low rules coverage (< 8 items = complex/unusual matchup)
        - Mid-game re-evaluation (lane_result set = needs deeper reasoning)
        - Screenshot enemy context present (nuanced data)
        - Large enemy team with multiple lane opponents (complex draft)
        """
        if len(rules_items) < 8:
            logger.debug("Escalation: low rules coverage (%d items)", len(rules_items))
            return True
        if request.lane_result is not None:
            logger.debug("Escalation: mid-game re-evaluation (lane_result=%s)", request.lane_result)
            return True
        if len(request.enemy_context) > 0:
            logger.debug("Escalation: enemy context from screenshot (%d heroes)", len(request.enemy_context))
            return True
        if len(request.lane_opponents) > 1 and len(request.all_opponents) > 3:
            logger.debug("Escalation: complex draft (lane=%d, total=%d opponents)",
                         len(request.lane_opponents), len(request.all_opponents))
            return True
        return False

    # ------------------------------------------------------------------
    # Budget info attachment
    # ------------------------------------------------------------------

    def _attach_budget_info(self, response: RecommendResponse) -> None:
        """Attach budget usage info to response if cost tracker is available."""
        if self.cost_tracker:
            usage = self.cost_tracker.get_usage()
            response.budget_used = usage["cost"]
            response.budget_limit = usage["budget"]

    # ------------------------------------------------------------------
    # Post-parse validation with retry
    # ------------------------------------------------------------------

    async def _validate_and_retry(
        self,
        phases: list[RecommendPhase],
        request: RecommendRequest,
        rules_items: list[RuleResult],
        db: AsyncSession,
        user_message: str,
    ) -> tuple[list[RecommendPhase], str | None, list | None]:
        """Validate LLM output. On error, retry once with error feedback.

        Returns (validated_phases, overall_strategy, neutral_items).
        If validation passes, returns (phases, None, None) -- caller keeps
        its own strategy/neutrals. If retry also fails validation, returns
        the retry result anyway (best-effort).
        """
        if not self.response_validator:
            return phases, None, None

        result = self.response_validator.validate(phases, request)
        if result.valid:
            return phases, None, None

        # Retry once: append error messages to user message
        error_feedback = (
            "\n\nYour previous recommendation had these issues, please correct:\n"
            + "\n".join(f"- {msg}" for msg in result.error_messages)
        )
        retry_message = user_message + error_feedback
        logger.info("Validation failed, retrying with %d error(s)", len(result.error_messages))

        llm_result, _ = await self.llm.generate(retry_message)
        if llm_result is None:
            # Retry failed to produce output, return original
            return phases, None, None

        retry_phases = self._merge(rules_items, llm_result)
        retry_phases = self._validate_item_ids(retry_phases)
        retry_phases = self._deduplicate_across_phases(retry_phases)

        # Validate retry result (log but don't retry again)
        retry_result = self.response_validator.validate(retry_phases, request)
        if not retry_result.valid:
            logger.warning(
                "Retry also failed validation (%d errors), using best-effort result",
                len(retry_result.error_messages),
            )

        return retry_phases, llm_result.overall_strategy, llm_result.neutral_items

    # ------------------------------------------------------------------
    # Shared enrichment pipeline
    # ------------------------------------------------------------------

    async def _enrich_all(
        self,
        request: RecommendRequest,
        phases: list[RecommendPhase],
        db: AsyncSession,
    ) -> tuple[list[ItemTimingResponse], list[BuildPathResponse], WinConditionResponse | None, float | None]:
        """Run all post-LLM enrichment steps in parallel."""
        if not self.cache:
            return [], [], None, None

        async def _timing() -> list[ItemTimingResponse]:
            return await self._enrich_timing_data(request.hero_id, phases, db)

        async def _build_paths() -> list[BuildPathResponse]:
            return self._enrich_build_paths(request, phases)

        async def _win_cond() -> WinConditionResponse | None:
            return self._enrich_win_condition(request)

        async def _win_prob() -> float | None:
            return self._enrich_win_probability(request)

        timing_data, build_paths, win_condition, win_probability = await asyncio.gather(
            _timing(), _build_paths(), _win_cond(), _win_prob()
        )
        return timing_data, build_paths, win_condition, win_probability

    # ------------------------------------------------------------------
    # Merge, rules-only, filter, validate (unchanged from original)
    # ------------------------------------------------------------------

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

    def _deduplicate_across_phases(
        self, phases: list[RecommendPhase]
    ) -> list[RecommendPhase]:
        """Remove items that appear in multiple phases. Earlier phase wins.

        Phase order follows the list order (starting, laning, core, late_game,
        situational). If the same item_id appears in core and late_game, the
        late_game duplicate is removed. Removes phases that become empty.
        """
        seen_ids: set[int] = set()
        deduped: list[RecommendPhase] = []
        for phase in phases:
            unique_items = []
            for item in phase.items:
                if item.item_id not in seen_ids:
                    seen_ids.add(item.item_id)
                    unique_items.append(item)
                else:
                    logger.debug(
                        "Removed cross-phase duplicate: %s (%d) in %s",
                        item.item_name, item.item_id, phase.phase,
                    )
            if unique_items:
                deduped.append(
                    RecommendPhase(
                        phase=phase.phase,
                        items=unique_items,
                        timing=phase.timing,
                        gold_budget=phase.gold_budget,
                    )
                )
        return deduped

    async def _enrich_timing_data(
        self, hero_id: int, phases: list[RecommendPhase], db: AsyncSession
    ) -> list[ItemTimingResponse]:
        """Build timing response data for all recommended items.

        Looks up timing benchmarks from DataCache, classifies zones,
        and returns pre-computed display data for the frontend.
        Falls back to on-demand fetch when cache is empty (DATA-03).
        """
        timings = self.cache.get_hero_timings(hero_id)
        if not timings:
            timings = await get_or_fetch_hero_timings(
                hero_id, db, self.context_builder.opendota
            )
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
                ontrack_win_rate=classified["ontrack_win_rate"],
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

    def _enrich_win_condition(
        self, request: RecommendRequest
    ) -> WinConditionResponse | None:
        """Classify allied and enemy team archetypes for frontend badge display.

        Post-LLM enrichment -- NOT generated by Claude. Uses same classify_draft
        logic as ContextBuilder._build_team_strategy_section() (pre-LLM context
        injection) so frontend badge matches what Claude was told.

        Returns None if neither team meets the 3-hero threshold.
        """
        if not self.cache:
            return None

        allied_ids = [request.hero_id] + list(request.allies)
        allied_result = classify_draft(allied_ids, self.cache)

        enemy_result = classify_draft(list(request.all_opponents), self.cache)

        if allied_result is None and enemy_result is None:
            return None

        return WinConditionResponse(
            allied_archetype=allied_result.archetype if allied_result else "unknown",
            allied_confidence=allied_result.confidence if allied_result else "low",
            enemy_archetype=enemy_result.archetype if enemy_result else None,
            enemy_confidence=enemy_result.confidence if enemy_result else None,
        )

    def _enrich_win_probability(self, request: RecommendRequest) -> float | None:
        """Compute statistical win probability from draft composition.

        Post-LLM enrichment -- NOT sent to Claude. Uses DataCache-held XGBoost models.
        Defaults to bracket_2 (Archon-Legend) when no MMR info in request.
        Returns None when fewer than 10 total heroes or models unavailable.
        """
        allied = [request.hero_id] + list(request.allies)
        enemies = list(request.all_opponents)
        is_radiant = request.side == "radiant"
        bracket = 2  # Default: Archon-Legend (most representative bracket)

        predictor = WinPredictor()
        return predictor.predict(
            allied_hero_ids=allied,
            enemy_hero_ids=enemies,
            is_radiant=is_radiant,
            bracket=bracket,
            cache=self.cache,
        )

    def _adjust_priorities_for_win_condition(
        self,
        phases: list[RecommendPhase],
        win_condition: WinConditionResponse,
    ) -> list[RecommendPhase]:
        """Adjust item priorities based on team win condition (WCON-03).

        Early-aggression archetypes (deathball, pick-off) deprioritize luxury
        late-game items. Scaling archetypes (late-game scale) keep luxury items
        but flag timing-sensitive mid-game items.
        """
        EARLY_ARCHETYPES = {"deathball", "pick-off"}
        archetype = win_condition.allied_archetype

        if archetype not in EARLY_ARCHETYPES:
            return phases

        # Downgrade luxury items to situational for early-win-condition drafts
        adjusted: list[RecommendPhase] = []
        for phase in phases:
            if phase.phase in ("late_game",):
                new_items = []
                for item in phase.items:
                    if item.priority == "luxury":
                        new_items.append(item.model_copy(update={"priority": "situational"}))
                    else:
                        new_items.append(item)
                adjusted.append(phase.model_copy(update={"items": new_items}))
            else:
                adjusted.append(phase)
        return adjusted

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
