"""Tests for the response cache in the recommender module."""

import time

import pytest

from engine.schemas import RecommendRequest, RecommendResponse


class TestResponseCache:
    def _make_request(self, hero_id=1):
        return RecommendRequest(
            hero_id=hero_id,
            role=1,
            playstyle="Aggressive",
            side="radiant",
            lane="safe",
        )

    def _make_response(self):
        return RecommendResponse(phases=[], overall_strategy="test", fallback=False)

    def test_cache_miss_returns_none(self):
        from engine.recommender import ResponseCache

        cache = ResponseCache(ttl_seconds=300)
        assert cache.get(self._make_request()) is None

    def test_cache_hit_returns_response(self):
        from engine.recommender import ResponseCache

        cache = ResponseCache(ttl_seconds=300)
        req = self._make_request()
        resp = self._make_response()
        cache.set(req, resp)
        assert cache.get(req) is not None
        assert cache.get(req).overall_strategy == "test"

    def test_cache_expired_returns_none(self):
        from engine.recommender import ResponseCache

        cache = ResponseCache(ttl_seconds=0.01)  # Very short TTL
        req = self._make_request()
        cache.set(req, self._make_response())
        time.sleep(0.02)
        assert cache.get(req) is None

    def test_different_requests_different_keys(self):
        from engine.recommender import ResponseCache

        cache = ResponseCache(ttl_seconds=300)
        req1 = self._make_request(hero_id=1)
        req2 = self._make_request(hero_id=2)
        cache.set(req1, self._make_response())
        assert cache.get(req1) is not None
        assert cache.get(req2) is None

    def test_cleanup_evicts_expired(self):
        from engine.recommender import ResponseCache

        cache = ResponseCache(ttl_seconds=0.01)
        cache.set(self._make_request(), self._make_response())
        time.sleep(0.02)
        cache.cleanup()
        assert len(cache._cache) == 0
