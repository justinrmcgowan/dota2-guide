"""Tests for the HybridRecommender orchestrator.

Covers merge logic, deduplication, fallback on LLM failure,
item ID validation against DB, and response metadata.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock

from engine.schemas import (
    RecommendRequest,
    RecommendResponse,
    RecommendPhase,
    ItemRecommendation,
    RuleResult,
    LLMRecommendation,
)
from engine.rules import RulesEngine
from engine.recommender import HybridRecommender


@pytest.fixture
def sample_request() -> RecommendRequest:
    """A standard Pos 1 Anti-Mage vs Bristleback request."""
    return RecommendRequest(
        hero_id=1,
        role=1,
        playstyle="farming",
        side="radiant",
        lane="safe",
        lane_opponents=[69],
        allies=[],
    )


@pytest.fixture
def mock_llm_engine():
    """Mock LLMEngine that returns a valid LLMRecommendation."""
    engine = MagicMock()
    engine.MODEL = "claude-sonnet-4-6-20250514"
    engine.generate = AsyncMock(return_value=LLMRecommendation(
        phases=[
            RecommendPhase(
                phase="laning",
                items=[
                    ItemRecommendation(
                        item_id=48,
                        item_name="Power Treads",
                        reasoning="Attack speed and stat switching for farming.",
                        priority="core",
                    ),
                ],
            ),
            RecommendPhase(
                phase="core",
                items=[
                    ItemRecommendation(
                        item_id=1,
                        item_name="Blink Dagger",
                        reasoning="Mobility for split-push and initiation.",
                        priority="core",
                    ),
                ],
            ),
        ],
        overall_strategy="Farm Battlefury then Manta, split-push aggressively.",
    ))
    return engine


@pytest.fixture
def mock_context_builder():
    """Mock ContextBuilder that returns a simple prompt string."""
    builder = MagicMock()
    builder.build = AsyncMock(return_value="Test prompt context")
    return builder


@pytest_asyncio.fixture
async def recommender_fixture(mock_llm_engine, mock_context_builder):
    """HybridRecommender with real RulesEngine, mocked LLM and ContextBuilder."""
    return HybridRecommender(
        rules=RulesEngine(),
        llm=mock_llm_engine,
        context_builder=mock_context_builder,
    )


# -------------------------------------------------------------------
# Merge logic tests
# -------------------------------------------------------------------


@pytest.mark.asyncio
async def test_hybrid_merge(recommender_fixture):
    """Merged output has rules items prepended to matching LLM phases."""
    recommender = recommender_fixture

    rules_items = [
        RuleResult(
            item_id=36,
            item_name="Magic Stick",
            reasoning="vs Bristleback",
            phase="laning",
            priority="core",
        ),
    ]

    llm_result = LLMRecommendation(
        phases=[
            RecommendPhase(
                phase="laning",
                items=[
                    ItemRecommendation(
                        item_id=48,
                        item_name="Power Treads",
                        reasoning="Attack speed and stat switching.",
                        priority="core",
                    ),
                ],
            ),
        ],
        overall_strategy="Farm aggressively.",
    )

    merged = recommender._merge(rules_items, llm_result)

    assert len(merged) == 1
    laning = merged[0]
    assert laning.phase == "laning"
    # Magic Stick should be first (rules take priority)
    assert laning.items[0].item_id == 36
    assert laning.items[0].item_name == "Magic Stick"
    # Power Treads follows
    assert laning.items[1].item_id == 48
    # No duplicate item_ids
    item_ids = [item.item_id for item in laning.items]
    assert len(item_ids) == len(set(item_ids))


@pytest.mark.asyncio
async def test_hybrid_merge_deduplication(recommender_fixture):
    """When rules and LLM both recommend the same item_id, keep only the rule version."""
    recommender = recommender_fixture

    rules_items = [
        RuleResult(
            item_id=36,
            item_name="Magic Stick",
            reasoning="Rules: vs Bristleback spell spam",
            phase="laning",
            priority="core",
        ),
    ]

    llm_result = LLMRecommendation(
        phases=[
            RecommendPhase(
                phase="laning",
                items=[
                    ItemRecommendation(
                        item_id=36,
                        item_name="Magic Stick",
                        reasoning="LLM: Good against frequent casters.",
                        priority="situational",
                    ),
                    ItemRecommendation(
                        item_id=48,
                        item_name="Power Treads",
                        reasoning="Attack speed.",
                        priority="core",
                    ),
                ],
            ),
        ],
        overall_strategy="Counter spell spam.",
    )

    merged = recommender._merge(rules_items, llm_result)

    laning = merged[0]
    # item_id=36 should appear exactly once
    ids_36 = [item for item in laning.items if item.item_id == 36]
    assert len(ids_36) == 1
    # And it should be the rule version (reasoning starts with "Rules:")
    assert "Rules:" in ids_36[0].reasoning
    # Total items: Magic Stick + Power Treads = 2
    assert len(laning.items) == 2


# -------------------------------------------------------------------
# Fallback tests
# -------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fallback_on_timeout(
    recommender_fixture, mock_llm_engine, sample_request, test_db_session
):
    """When LLM returns None, response.fallback is True and rules-only results present."""
    mock_llm_engine.generate = AsyncMock(return_value=None)

    response = await recommender_fixture.recommend(sample_request, test_db_session)

    assert response.fallback is True
    assert response.model is None
    assert len(response.phases) > 0  # Rules should produce results


@pytest.mark.asyncio
async def test_fallback_flag(
    recommender_fixture, mock_llm_engine, sample_request, test_db_session
):
    """When LLM raises an exception, response.fallback is True."""
    mock_llm_engine.generate = AsyncMock(side_effect=Exception("API down"))

    response = await recommender_fixture.recommend(sample_request, test_db_session)

    assert response.fallback is True


# -------------------------------------------------------------------
# Item validation tests
# -------------------------------------------------------------------


@pytest.mark.asyncio
async def test_invalid_item_id_filtered(recommender_fixture, test_db_session):
    """Items with IDs not in the DB are filtered out of results."""
    phases = [
        RecommendPhase(
            phase="laning",
            items=[
                ItemRecommendation(
                    item_id=36,
                    item_name="Magic Stick",
                    reasoning="Valid item",
                    priority="core",
                ),
                ItemRecommendation(
                    item_id=99999,
                    item_name="Hallucinated Item",
                    reasoning="Does not exist",
                    priority="core",
                ),
            ],
        ),
    ]

    validated = await recommender_fixture._validate_item_ids(phases, test_db_session)

    assert len(validated) == 1
    all_ids = [item.item_id for item in validated[0].items]
    assert 99999 not in all_ids
    assert 36 in all_ids


# -------------------------------------------------------------------
# Rules-only grouping test
# -------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rules_only_groups_by_phase(recommender_fixture):
    """_rules_only groups RuleResults by phase into separate RecommendPhases."""
    rules_items = [
        RuleResult(
            item_id=36,
            item_name="Magic Stick",
            reasoning="vs spell spam",
            phase="laning",
            priority="core",
        ),
        RuleResult(
            item_id=48,
            item_name="Power Treads",
            reasoning="boots",
            phase="laning",
            priority="core",
        ),
        RuleResult(
            item_id=116,
            item_name="Black King Bar",
            reasoning="vs magic",
            phase="core",
            priority="core",
        ),
    ]

    phases = recommender_fixture._rules_only(rules_items)

    assert len(phases) == 2
    phase_names = [p.phase for p in phases]
    assert "laning" in phase_names
    assert "core" in phase_names

    laning_phase = next(p for p in phases if p.phase == "laning")
    assert len(laning_phase.items) == 2

    core_phase = next(p for p in phases if p.phase == "core")
    assert len(core_phase.items) == 1


# -------------------------------------------------------------------
# Metadata tests
# -------------------------------------------------------------------


@pytest.mark.asyncio
async def test_latency_ms_populated(
    recommender_fixture, sample_request, test_db_session
):
    """Response includes latency_ms as a positive integer."""
    response = await recommender_fixture.recommend(sample_request, test_db_session)

    assert isinstance(response.latency_ms, int)
    assert response.latency_ms >= 0


@pytest.mark.asyncio
async def test_overall_strategy_on_fallback(
    recommender_fixture, mock_llm_engine, sample_request, test_db_session
):
    """On fallback, overall_strategy indicates rules-only mode."""
    mock_llm_engine.generate = AsyncMock(return_value=None)

    response = await recommender_fixture.recommend(sample_request, test_db_session)

    assert response.overall_strategy is not None
    assert "unavailable" in response.overall_strategy.lower() or \
           "rules-based" in response.overall_strategy.lower()
