"""Unit tests for diff-based context building and eval snapshot lifecycle.

Tests EvalSnapshot creation, build_diff() behavior (opponent change fallback,
diff generation, header format, token savings), and _is_reevaluation detection.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from data.cache import data_cache
from engine.context_builder import ContextBuilder, EvalSnapshot
from engine.schemas import RecommendRequest, RecommendResponse, RuleResult, EnemyContext
from engine.recommender import HybridRecommender


def _make_request(**kwargs) -> RecommendRequest:
    """Create a minimal valid RecommendRequest for testing."""
    defaults = dict(
        hero_id=1,
        role=1,
        playstyle="Farm-first",
        side="radiant",
        lane="safe",
        lane_opponents=[],
        allies=[],
        all_opponents=[],
    )
    defaults.update(kwargs)
    return RecommendRequest(**defaults)


@pytest.fixture
def builder():
    """ContextBuilder with a mock OpenDota client and DataCache singleton."""
    mock_opendota = MagicMock()
    return ContextBuilder(opendota_client=mock_opendota, cache=data_cache)


@pytest.fixture
def mock_db():
    """Mock async DB session."""
    return AsyncMock()


# ---------------------------------------------------------------------------
# Test 1: EvalSnapshot.from_request creates correct snapshot
# ---------------------------------------------------------------------------


class TestEvalSnapshotFromRequest:
    def test_creates_snapshot_from_request(self):
        """EvalSnapshot.from_request captures all key fields from RecommendRequest."""
        req = _make_request(
            hero_id=1,
            role=1,
            lane_opponents=[2, 3],
            allies=[4, 5],
            all_opponents=[2, 3, 6, 7, 8],
            lane_result="won",
            damage_profile={"physical": 60, "magical": 30, "pure": 10},
            enemy_items_spotted=["bkb", "blink"],
            purchased_items=[36, 48],
            game_time_seconds=600,
            turbo=False,
        )
        full_ctx = "some full context string"
        snap = EvalSnapshot.from_request(req, full_ctx)

        assert snap.hero_id == 1
        assert snap.role == 1
        assert snap.lane_opponents == tuple(sorted([2, 3]))
        assert snap.allies == tuple(sorted([4, 5]))
        assert snap.all_opponents == tuple(sorted([2, 3, 6, 7, 8]))
        assert snap.lane_result == "won"
        assert snap.damage_profile is not None
        assert snap.enemy_items_spotted == tuple(sorted(["bkb", "blink"]))
        assert snap.purchased_items == tuple(sorted([36, 48]))
        assert snap.game_time_seconds == 600
        assert snap.turbo is False
        assert snap.full_context == full_ctx

    def test_snapshot_enemy_context_hash_empty(self):
        """Empty enemy_context produces empty hash string."""
        req = _make_request(enemy_context=[])
        snap = EvalSnapshot.from_request(req, "ctx")
        assert snap.enemy_context_hash == ""

    def test_snapshot_enemy_context_hash_populated(self):
        """Non-empty enemy_context produces a non-empty MD5 hash."""
        req = _make_request(
            enemy_context=[
                EnemyContext(hero_id=2, kills=5, deaths=1, assists=3, level=10),
            ]
        )
        snap = EvalSnapshot.from_request(req, "ctx")
        assert snap.enemy_context_hash != ""
        assert len(snap.enemy_context_hash) == 32  # MD5 hex digest


# ---------------------------------------------------------------------------
# Test 2: build_diff returns None when opponents change
# ---------------------------------------------------------------------------


class TestBuildDiffOpponentChange:
    @pytest.mark.asyncio
    async def test_returns_none_when_lane_opponents_change(self, builder, mock_db):
        """build_diff returns None when lane_opponents differ from prior snapshot."""
        initial_req = _make_request(
            lane_opponents=[2],
            all_opponents=[2, 3, 4, 5, 6],
        )
        initial_ctx = await builder.build(initial_req, [], mock_db)
        prior = EvalSnapshot.from_request(initial_req, initial_ctx)

        # Changed lane opponents
        new_req = _make_request(
            lane_opponents=[3],
            all_opponents=[2, 3, 4, 5, 6],
            lane_result="won",
        )
        result = await builder.build_diff(new_req, [], mock_db, prior)
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_all_opponents_change(self, builder, mock_db):
        """build_diff returns None when all_opponents differ from prior snapshot."""
        initial_req = _make_request(
            lane_opponents=[2],
            all_opponents=[2, 3, 4, 5, 6],
        )
        initial_ctx = await builder.build(initial_req, [], mock_db)
        prior = EvalSnapshot.from_request(initial_req, initial_ctx)

        # Changed all_opponents
        new_req = _make_request(
            lane_opponents=[2],
            all_opponents=[2, 3, 4, 5, 7],  # hero 7 instead of 6
            lane_result="won",
        )
        result = await builder.build_diff(new_req, [], mock_db, prior)
        assert result is None


# ---------------------------------------------------------------------------
# Test 3: build_diff returns None when allies change
# ---------------------------------------------------------------------------


class TestBuildDiffAllyChange:
    @pytest.mark.asyncio
    async def test_returns_none_when_allies_change(self, builder, mock_db):
        """build_diff returns None when allies differ from prior snapshot."""
        initial_req = _make_request(
            allies=[3, 4],
            lane_opponents=[2],
            all_opponents=[2],
        )
        initial_ctx = await builder.build(initial_req, [], mock_db)
        prior = EvalSnapshot.from_request(initial_req, initial_ctx)

        new_req = _make_request(
            allies=[3, 5],  # ally changed
            lane_opponents=[2],
            all_opponents=[2],
            lane_result="won",
        )
        result = await builder.build_diff(new_req, [], mock_db, prior)
        assert result is None


# ---------------------------------------------------------------------------
# Test 4: build_diff returns compact diff when only lane_result changes
# ---------------------------------------------------------------------------


class TestBuildDiffLaneResult:
    @pytest.mark.asyncio
    async def test_diff_includes_lane_result_change(self, builder, mock_db):
        """build_diff includes lane result change in diff output."""
        initial_req = _make_request(
            lane_opponents=[2],
            all_opponents=[2],
        )
        initial_ctx = await builder.build(initial_req, [], mock_db)
        prior = EvalSnapshot.from_request(initial_req, initial_ctx)

        new_req = _make_request(
            lane_opponents=[2],
            all_opponents=[2],
            lane_result="won",
        )
        result = await builder.build_diff(new_req, [], mock_db, prior)
        assert result is not None
        assert "Lane Result: won" in result


# ---------------------------------------------------------------------------
# Test 5: build_diff returns compact diff when enemy_items_spotted gains new items
# ---------------------------------------------------------------------------


class TestBuildDiffEnemyItems:
    @pytest.mark.asyncio
    async def test_diff_includes_new_enemy_items(self, builder, mock_db):
        """build_diff shows only new enemy items (set difference)."""
        initial_req = _make_request(
            lane_opponents=[2],
            all_opponents=[2],
            enemy_items_spotted=["blink"],
        )
        initial_ctx = await builder.build(initial_req, [], mock_db)
        prior = EvalSnapshot.from_request(initial_req, initial_ctx)

        new_req = _make_request(
            lane_opponents=[2],
            all_opponents=[2],
            enemy_items_spotted=["blink", "bkb"],
            lane_result=None,
            game_time_seconds=600,  # need a mid-game field for the diff to detect
        )
        result = await builder.build_diff(new_req, [], mock_db, prior)
        assert result is not None
        assert "Bkb" in result or "BKB" in result or "Black King Bar" in result or "New Enemy Items" in result


# ---------------------------------------------------------------------------
# Test 6: build_diff includes "Re-Evaluation Context" header
# ---------------------------------------------------------------------------


class TestBuildDiffHeader:
    @pytest.mark.asyncio
    async def test_diff_has_re_evaluation_header(self, builder, mock_db):
        """build_diff output starts with Re-Evaluation Context header."""
        initial_req = _make_request(
            lane_opponents=[2],
            all_opponents=[2],
        )
        initial_ctx = await builder.build(initial_req, [], mock_db)
        prior = EvalSnapshot.from_request(initial_req, initial_ctx)

        new_req = _make_request(
            lane_opponents=[2],
            all_opponents=[2],
            lane_result="lost",
        )
        result = await builder.build_diff(new_req, [], mock_db, prior)
        assert result is not None
        assert "Re-Evaluation Context" in result


# ---------------------------------------------------------------------------
# Test 7: build_diff omits item catalog, popularity, timing sections
# ---------------------------------------------------------------------------


class TestBuildDiffOmitsSections:
    @pytest.mark.asyncio
    async def test_diff_omits_static_sections(self, builder, mock_db):
        """build_diff does NOT contain item catalog, popularity, or timing headers."""
        initial_req = _make_request(
            lane_opponents=[2],
            all_opponents=[2],
        )
        initial_ctx = await builder.build(initial_req, [], mock_db)
        prior = EvalSnapshot.from_request(initial_req, initial_ctx)

        new_req = _make_request(
            lane_opponents=[2],
            all_opponents=[2],
            lane_result="even",
        )
        result = await builder.build_diff(new_req, [], mock_db, prior)
        assert result is not None

        # These sections should be in full context but NOT in diff
        assert "## Available Items" not in result
        assert "## Popular Items" not in result
        assert "## Item Timing Benchmarks" not in result
        assert "## Gold-Standard Examples" not in result
        assert "## Neutral Items Catalog" not in result
        assert "## What Divine/Immortal" not in result


# ---------------------------------------------------------------------------
# Test 8: _is_reevaluation returns False for fresh draft request
# ---------------------------------------------------------------------------


class TestIsReevaluation:
    def test_fresh_draft_is_not_reevaluation(self):
        """A fresh draft request with no mid-game fields is not a re-evaluation."""
        req = _make_request()
        assert HybridRecommender._is_reevaluation(req) is False

    def test_lane_result_is_reevaluation(self):
        """Request with lane_result set is a re-evaluation."""
        req = _make_request(lane_result="won")
        assert HybridRecommender._is_reevaluation(req) is True

    def test_purchased_items_is_reevaluation(self):
        """Request with purchased_items is a re-evaluation."""
        req = _make_request(purchased_items=[36])
        assert HybridRecommender._is_reevaluation(req) is True

    def test_damage_profile_is_reevaluation(self):
        """Request with damage_profile set is a re-evaluation."""
        req = _make_request(damage_profile={"physical": 60, "magical": 30, "pure": 10})
        assert HybridRecommender._is_reevaluation(req) is True

    def test_enemy_items_spotted_is_reevaluation(self):
        """Request with enemy_items_spotted is a re-evaluation."""
        req = _make_request(enemy_items_spotted=["bkb"])
        assert HybridRecommender._is_reevaluation(req) is True

    def test_game_time_is_reevaluation(self):
        """Request with positive game_time_seconds is a re-evaluation."""
        req = _make_request(game_time_seconds=300)
        assert HybridRecommender._is_reevaluation(req) is True

    def test_game_time_zero_is_not_reevaluation(self):
        """Request with game_time_seconds=0 is not a re-evaluation (pre-game)."""
        req = _make_request(game_time_seconds=0)
        assert HybridRecommender._is_reevaluation(req) is False


# ---------------------------------------------------------------------------
# Test 11: Diff context is at least 40% shorter than full context
# ---------------------------------------------------------------------------


class TestDiffTokenReduction:
    @pytest.mark.asyncio
    @pytest.mark.usefixtures("test_db_setup")
    async def test_diff_at_least_40_percent_shorter(self):
        """Diff context is at least 40% shorter than full context for same matchup.

        Uses test_db_setup to load real heroes/items into DataCache, ensuring
        the full context includes item catalog, hero names, and other sections
        that build_diff intentionally omits.
        """
        from tests.conftest import test_async_session

        mock_opendota = MagicMock()
        cb = ContextBuilder(opendota_client=mock_opendota, cache=data_cache)

        async with test_async_session() as session:
            # Build full context for initial request (hero 1 = Anti-Mage, opponent 2 = Axe)
            initial_req = _make_request(
                hero_id=1,
                role=1,
                lane="safe",
                lane_opponents=[2],
                all_opponents=[2, 3],
            )
            full_context = await cb.build(initial_req, [], session)

            # Create a snapshot from the full context
            prior = EvalSnapshot.from_request(initial_req, full_context)

            # Re-evaluation with mid-game changes
            reeval_req = _make_request(
                hero_id=1,
                role=1,
                lane="safe",
                lane_opponents=[2],
                all_opponents=[2, 3],
                lane_result="won",
                enemy_items_spotted=["bkb"],
                purchased_items=[36],
                game_time_seconds=900,
            )

            diff_context = await cb.build_diff(reeval_req, [], session, prior)
            assert diff_context is not None

            # Diff should be at least 40% shorter
            reduction = 1 - (len(diff_context) / len(full_context))
            assert reduction >= 0.40, (
                f"Diff context only {reduction*100:.1f}% shorter than full context "
                f"(full={len(full_context)}, diff={len(diff_context)})"
            )
