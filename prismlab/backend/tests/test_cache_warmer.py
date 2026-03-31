"""Tests for CacheWarmer module -- pre-computes rules-only recs for popular hero+role combos."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from engine.schemas import RecommendResponse


def _make_response(strategy: str = "test") -> RecommendResponse:
    return RecommendResponse(phases=[], overall_strategy=strategy, fallback=False)


class TestGetWarmableCombos:
    """get_warmable_combos() returns correct hero+role+lane tuples."""

    def test_returns_combos_from_hero_role_viable(self):
        from engine.cache_warmer import CacheWarmer

        warmer = CacheWarmer(recommender=MagicMock(), cache=MagicMock())
        combos = warmer.get_warmable_combos()

        assert len(combos) > 0, "Should return at least one combo"
        # Each combo is (hero_id, role, lane)
        for hero_id, role, lane in combos:
            assert isinstance(hero_id, int)
            assert role in (1, 2, 3, 4, 5)
            assert lane in ("safe", "mid", "off")

    def test_lane_mapping_pos1_safe(self):
        from engine.cache_warmer import CacheWarmer

        warmer = CacheWarmer(recommender=MagicMock(), cache=MagicMock())
        combos = warmer.get_warmable_combos()

        # All pos 1 combos should have lane "safe"
        pos1_combos = [(h, r, l) for h, r, l in combos if r == 1]
        assert len(pos1_combos) > 0
        for _, _, lane in pos1_combos:
            assert lane == "safe"

    def test_lane_mapping_pos2_mid(self):
        from engine.cache_warmer import CacheWarmer

        warmer = CacheWarmer(recommender=MagicMock(), cache=MagicMock())
        combos = warmer.get_warmable_combos()

        pos2_combos = [(h, r, l) for h, r, l in combos if r == 2]
        assert len(pos2_combos) > 0
        for _, _, lane in pos2_combos:
            assert lane == "mid"

    def test_lane_mapping_pos3_off(self):
        from engine.cache_warmer import CacheWarmer

        warmer = CacheWarmer(recommender=MagicMock(), cache=MagicMock())
        combos = warmer.get_warmable_combos()

        pos3_combos = [(h, r, l) for h, r, l in combos if r == 3]
        assert len(pos3_combos) > 0
        for _, _, lane in pos3_combos:
            assert lane == "off"

    def test_lane_mapping_pos4_off(self):
        from engine.cache_warmer import CacheWarmer

        warmer = CacheWarmer(recommender=MagicMock(), cache=MagicMock())
        combos = warmer.get_warmable_combos()

        pos4_combos = [(h, r, l) for h, r, l in combos if r == 4]
        assert len(pos4_combos) > 0
        for _, _, lane in pos4_combos:
            assert lane == "off"

    def test_lane_mapping_pos5_safe(self):
        from engine.cache_warmer import CacheWarmer

        warmer = CacheWarmer(recommender=MagicMock(), cache=MagicMock())
        combos = warmer.get_warmable_combos()

        pos5_combos = [(h, r, l) for h, r, l in combos if r == 5]
        assert len(pos5_combos) > 0
        for _, _, lane in pos5_combos:
            assert lane == "safe"

    def test_combo_count_approximately_90(self):
        """HERO_ROLE_VIABLE should produce roughly 90 combos (varies with heroPlaystyles.ts)."""
        from engine.cache_warmer import CacheWarmer

        warmer = CacheWarmer(recommender=MagicMock(), cache=MagicMock())
        combos = warmer.get_warmable_combos()

        # There are ~130 entries in _HERO_PLAYSTYLE_ENTRIES
        assert 80 <= len(combos) <= 200, f"Expected ~90-130 combos, got {len(combos)}"


class TestWarm:
    """warm() generates requests and calls set_l1 for each successful combo."""

    @pytest.mark.asyncio
    async def test_warm_calls_set_l1_for_each_combo(self):
        from engine.cache_warmer import CacheWarmer

        mock_recommender = MagicMock()
        mock_response = _make_response("warmed")
        mock_recommender._fast_path = AsyncMock(return_value=mock_response)

        mock_cache = MagicMock()

        warmer = CacheWarmer(recommender=mock_recommender, cache=mock_cache)
        combos = warmer.get_warmable_combos()

        mock_db = AsyncMock()
        warmed = await warmer.warm(mock_db)

        assert warmed == len(combos)
        assert mock_cache.set_l1.call_count == len(combos)

    @pytest.mark.asyncio
    async def test_warm_continues_on_individual_failure(self):
        from engine.cache_warmer import CacheWarmer

        call_count = 0

        async def _fast_path_with_failure(request, db):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("simulated failure")
            return _make_response("warmed")

        mock_recommender = MagicMock()
        mock_recommender._fast_path = AsyncMock(side_effect=_fast_path_with_failure)

        mock_cache = MagicMock()
        warmer = CacheWarmer(recommender=mock_recommender, cache=mock_cache)
        combos = warmer.get_warmable_combos()

        mock_db = AsyncMock()
        warmed = await warmer.warm(mock_db)

        # One combo failed, rest should succeed
        assert warmed == len(combos) - 1
        assert mock_cache.set_l1.call_count == len(combos) - 1

    @pytest.mark.asyncio
    async def test_warm_uses_deterministic_playstyle(self):
        """Each request should use the alphabetically first playstyle for that role."""
        from engine.cache_warmer import CacheWarmer
        from engine.schemas import VALID_PLAYSTYLES

        captured_requests = []

        async def _capture_fast_path(request, db):
            captured_requests.append(request)
            return _make_response("warmed")

        mock_recommender = MagicMock()
        mock_recommender._fast_path = AsyncMock(side_effect=_capture_fast_path)

        mock_cache = MagicMock()
        warmer = CacheWarmer(recommender=mock_recommender, cache=mock_cache)

        mock_db = AsyncMock()
        await warmer.warm(mock_db)

        # Check that each request uses the alphabetically first playstyle for its role
        for req in captured_requests:
            expected_playstyle = sorted(VALID_PLAYSTYLES[req.role])[0]
            assert req.playstyle == expected_playstyle, (
                f"Role {req.role}: expected '{expected_playstyle}', got '{req.playstyle}'"
            )

    @pytest.mark.asyncio
    async def test_warm_uses_fast_mode(self):
        """Each request should use mode='fast' for rules-only path."""
        from engine.cache_warmer import CacheWarmer

        captured_requests = []

        async def _capture_fast_path(request, db):
            captured_requests.append(request)
            return _make_response("warmed")

        mock_recommender = MagicMock()
        mock_recommender._fast_path = AsyncMock(side_effect=_capture_fast_path)

        mock_cache = MagicMock()
        warmer = CacheWarmer(recommender=mock_recommender, cache=mock_cache)

        mock_db = AsyncMock()
        await warmer.warm(mock_db)

        for req in captured_requests:
            assert req.mode == "fast", f"Expected mode='fast', got '{req.mode}'"
