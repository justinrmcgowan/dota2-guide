"""Hybrid recommendation orchestrator.

Coordinates the rules engine (deterministic, instant) and LLM engine (Claude API,
structured output) into a unified recommendation pipeline with merge, deduplication,
fallback, and item ID validation.
"""

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
from engine.llm import LLMEngine
from engine.context_builder import ContextBuilder
from data.models import Item

logger = logging.getLogger(__name__)


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
    ):
        self.rules = rules
        self.llm = llm
        self.context_builder = context_builder

    async def recommend(
        self, request: RecommendRequest, db: AsyncSession
    ) -> RecommendResponse:
        """Run full hybrid recommendation pipeline.

        1. Rules engine fires instantly (deterministic)
        2. Context builder assembles Claude prompt
        3. Claude API generates structured recommendations
        4. Merge rules + LLM results (rules take priority, deduplicate)
        5. Validate all item_ids against DB
        6. Return response with metadata (fallback, model, latency_ms)
        """
        start = time.monotonic()

        # Step 1: Rules fire instantly (deterministic, no API call)
        rules_items = self.rules.evaluate(request)
        logger.info("Rules engine produced %d recommendations", len(rules_items))

        # Step 2: Build Claude prompt context
        user_message = await self.context_builder.build(request, rules_items, db)

        # Step 3: Call Claude with timeout + fallback
        llm_result: LLMRecommendation | None = None
        fallback = False
        try:
            llm_result = await self.llm.generate(user_message)
        except Exception as e:
            logger.exception("LLM engine failed: %s", e)
            fallback = True

        if llm_result is None:
            fallback = True

        # Step 4: Merge results
        if llm_result and not fallback:
            phases = self._merge(rules_items, llm_result)
            overall_strategy = llm_result.overall_strategy
        else:
            phases = self._rules_only(rules_items)
            overall_strategy = "Rules-based recommendations only. AI reasoning unavailable."

        # Step 5: Validate all item_ids against DB
        phases = await self._validate_item_ids(phases, db)

        elapsed_ms = int((time.monotonic() - start) * 1000)
        return RecommendResponse(
            phases=phases,
            overall_strategy=overall_strategy,
            fallback=fallback,
            model=LLMEngine.MODEL if not fallback else None,
            latency_ms=elapsed_ms,
        )

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

    async def _validate_item_ids(
        self, phases: list[RecommendPhase], db: AsyncSession
    ) -> list[RecommendPhase]:
        """Validate all item_ids against the Item table. Filter out invalid ones.

        Logs a warning for each filtered-out item. Removes empty phases.
        """
        result = await db.execute(select(Item.id, Item.cost))
        cost_map: dict[int, int | None] = {row[0]: row[1] for row in result.fetchall()}

        validated_phases: list[RecommendPhase] = []
        for phase in phases:
            valid_items: list[ItemRecommendation] = []
            for item in phase.items:
                if item.item_id in cost_map:
                    valid_items.append(
                        item.model_copy(update={"gold_cost": cost_map.get(item.item_id)})
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
