"""Tests for HierarchicalCache with L1/L2/L3 tiers."""

import time

import pytest

from engine.schemas import RecommendRequest, RecommendResponse


def _make_request(
    hero_id: int = 1,
    role: int = 1,
    lane: str = "safe",
    lane_opponents: list[int] | None = None,
    all_opponents: list[int] | None = None,
    playstyle: str = "Aggressive",
    side: str = "radiant",
    **kwargs,
) -> RecommendRequest:
    return RecommendRequest(
        hero_id=hero_id,
        role=role,
        playstyle=playstyle,
        side=side,
        lane=lane,
        lane_opponents=lane_opponents or [],
        all_opponents=all_opponents or [],
        **kwargs,
    )


def _make_response(strategy: str = "test") -> RecommendResponse:
    return RecommendResponse(phases=[], overall_strategy=strategy, fallback=False)


class TestHierarchicalCacheL3:
    """L3: exact request match."""

    def test_l3_exact_match_returns_cached_response(self):
        from engine.recommender import HierarchicalCache

        cache = HierarchicalCache()
        req = _make_request()
        resp = _make_response("exact hit")
        cache.set(req, resp)
        result = cache.get(req)
        assert result is not None
        assert result.overall_strategy == "exact hit"

    def test_l3_miss_returns_none(self):
        from engine.recommender import HierarchicalCache

        cache = HierarchicalCache()
        assert cache.get(_make_request()) is None

    def test_l3_expired_falls_through(self):
        from engine.recommender import HierarchicalCache

        cache = HierarchicalCache(l1_ttl=3600.0, l2_ttl=0.01, l3_ttl=0.01)
        req = _make_request()
        cache.set(req, _make_response("expired"))
        time.sleep(0.02)
        # L3 and L2 expired, but L1 still alive (1h TTL)
        result = cache.get(req)
        assert result is not None  # Falls through to L1


class TestHierarchicalCacheL2:
    """L2: matchup-level match (hero+role+lane+sorted opponents)."""

    def test_l2_hit_when_l3_misses(self):
        from engine.recommender import HierarchicalCache

        cache = HierarchicalCache()
        # Set cache with one request
        req1 = _make_request(
            lane_opponents=[2, 3],
            all_opponents=[2, 3, 4, 5, 6],
            purchased_items=[100],
        )
        cache.set(req1, _make_response("matchup hit"))

        # Different request but same hero+role+lane+opponents
        req2 = _make_request(
            lane_opponents=[2, 3],
            all_opponents=[2, 3, 4, 5, 6],
            purchased_items=[200],  # Different field -> L3 miss
        )
        result = cache.get(req2)
        assert result is not None
        assert result.overall_strategy == "matchup hit"

    def test_l2_miss_with_different_opponents(self):
        from engine.recommender import HierarchicalCache

        cache = HierarchicalCache(l1_ttl=0.01)  # Short L1 TTL to isolate L2
        req1 = _make_request(
            lane_opponents=[2, 3],
            all_opponents=[2, 3, 4, 5, 6],
        )
        cache.set(req1, _make_response("should not match"))
        time.sleep(0.02)  # Let L1 expire

        req2 = _make_request(
            lane_opponents=[7, 8],
            all_opponents=[7, 8, 9, 10, 11],
        )
        result = cache.get(req2)
        assert result is None


class TestHierarchicalCacheL1:
    """L1: hero+role+lane match."""

    def test_l1_hit_when_l2_and_l3_miss(self):
        from engine.recommender import HierarchicalCache

        cache = HierarchicalCache(l2_ttl=0.01, l3_ttl=0.01)
        req1 = _make_request(
            lane_opponents=[2, 3],
            all_opponents=[2, 3, 4, 5, 6],
        )
        cache.set(req1, _make_response("hero build"))
        time.sleep(0.02)  # L2 and L3 expire

        # Completely different opponents -> L2 miss, but same hero+role+lane -> L1 hit
        req2 = _make_request(
            lane_opponents=[7, 8],
            all_opponents=[7, 8, 9, 10, 11],
        )
        result = cache.get(req2)
        assert result is not None
        assert result.overall_strategy == "hero build"

    def test_l1_miss_with_different_hero(self):
        from engine.recommender import HierarchicalCache

        cache = HierarchicalCache(l2_ttl=0.01, l3_ttl=0.01)
        req1 = _make_request(hero_id=1)
        cache.set(req1, _make_response("wrong hero"))
        time.sleep(0.02)

        req2 = _make_request(hero_id=2)
        result = cache.get(req2)
        assert result is None


class TestHierarchicalCacheTTLs:
    """TTL configuration tests."""

    def test_default_ttls(self):
        from engine.recommender import HierarchicalCache

        cache = HierarchicalCache()
        assert cache.l1_ttl == 3600.0
        assert cache.l2_ttl == 300.0
        assert cache.l3_ttl == 300.0

    def test_custom_ttls(self):
        from engine.recommender import HierarchicalCache

        cache = HierarchicalCache(l1_ttl=7200.0, l2_ttl=600.0, l3_ttl=120.0)
        assert cache.l1_ttl == 7200.0
        assert cache.l2_ttl == 600.0
        assert cache.l3_ttl == 120.0


class TestHierarchicalCacheSetPopulatesAllTiers:
    """set() populates all three tiers from a single request+response pair."""

    def test_set_populates_all_tiers(self):
        from engine.recommender import HierarchicalCache

        cache = HierarchicalCache()
        req = _make_request(lane_opponents=[2], all_opponents=[2, 3, 4])
        cache.set(req, _make_response("all tiers"))
        assert len(cache._l1) == 1
        assert len(cache._l2) == 1
        assert len(cache._l3) == 1


class TestHierarchicalCacheCleanup:
    """cleanup() evicts expired entries from all tiers."""

    def test_cleanup_evicts_expired_from_all_tiers(self):
        from engine.recommender import HierarchicalCache

        cache = HierarchicalCache(l1_ttl=0.01, l2_ttl=0.01, l3_ttl=0.01)
        req = _make_request()
        cache.set(req, _make_response("ephemeral"))
        time.sleep(0.02)
        cache.cleanup()
        assert len(cache._l1) == 0
        assert len(cache._l2) == 0
        assert len(cache._l3) == 0

    def test_cleanup_keeps_valid_entries(self):
        from engine.recommender import HierarchicalCache

        cache = HierarchicalCache(l1_ttl=3600.0, l2_ttl=0.01, l3_ttl=0.01)
        req = _make_request()
        cache.set(req, _make_response("keep L1"))
        time.sleep(0.02)
        cache.cleanup()
        assert len(cache._l1) == 1  # 1h TTL, still valid
        assert len(cache._l2) == 0  # expired
        assert len(cache._l3) == 0  # expired


class TestHierarchicalCacheClear:
    """clear() empties all three tiers."""

    def test_clear_empties_all_tiers(self):
        from engine.recommender import HierarchicalCache

        cache = HierarchicalCache()
        req = _make_request()
        cache.set(req, _make_response("gone"))
        cache.clear()
        assert len(cache._l1) == 0
        assert len(cache._l2) == 0
        assert len(cache._l3) == 0
        assert cache.get(req) is None


class TestHierarchicalCacheSetL1:
    """set_l1() direct L1 write for cache warming."""

    def test_set_l1_direct_write(self):
        from engine.recommender import HierarchicalCache

        cache = HierarchicalCache()
        resp = _make_response("warmed")
        cache.set_l1(hero_id=1, role=1, lane="safe", response=resp)
        # L1 should be populated
        assert len(cache._l1) == 1
        # Should be retrievable via a request with same hero+role+lane
        req = _make_request(hero_id=1, role=1, lane="safe")
        result = cache.get(req)
        assert result is not None
        assert result.overall_strategy == "warmed"

    def test_set_l1_does_not_populate_l2_l3(self):
        from engine.recommender import HierarchicalCache

        cache = HierarchicalCache()
        cache.set_l1(hero_id=1, role=1, lane="safe", response=_make_response("l1 only"))
        assert len(cache._l2) == 0
        assert len(cache._l3) == 0


class TestHierarchicalCacheFallthrough:
    """Best available tier is served; higher tiers do not block."""

    def test_l3_preferred_over_l2_and_l1(self):
        from engine.recommender import HierarchicalCache

        cache = HierarchicalCache()
        req = _make_request()
        # Populate L1 separately with a different strategy
        cache.set_l1(hero_id=req.hero_id, role=req.role, lane=req.lane,
                     response=_make_response("L1 generic"))
        # Now set via full request (populates all 3 tiers)
        cache.set(req, _make_response("L3 exact"))
        result = cache.get(req)
        # L3 should win since it matches exactly
        assert result is not None
        assert result.overall_strategy == "L3 exact"

    def test_all_tiers_miss_returns_none(self):
        from engine.recommender import HierarchicalCache

        cache = HierarchicalCache()
        assert cache.get(_make_request()) is None
