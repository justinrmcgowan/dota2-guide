"""Tests for the per-IP rate limiter middleware."""

import pytest
from unittest.mock import MagicMock

from middleware.rate_limiter import InMemoryRateLimiter


class TestRateLimiter:
    def test_first_request_passes(self):
        """First request from an IP should not be rate limited."""
        limiter = InMemoryRateLimiter(cooldown_seconds=10.0)
        request = MagicMock()
        request.client.host = "127.0.0.1"
        request.headers = {}
        limiter.check(request)  # Should not raise

    def test_second_request_within_cooldown_raises_429(self):
        """Second request from same IP within cooldown raises HTTPException 429."""
        from fastapi import HTTPException

        limiter = InMemoryRateLimiter(cooldown_seconds=10.0)
        request = MagicMock()
        request.client.host = "127.0.0.1"
        request.headers = {}
        limiter.check(request)
        with pytest.raises(HTTPException) as exc_info:
            limiter.check(request)
        assert exc_info.value.status_code == 429
        assert "Retry-After" in exc_info.value.headers

    def test_different_ips_not_affected(self):
        """Requests from different IPs should not affect each other."""
        limiter = InMemoryRateLimiter(cooldown_seconds=10.0)
        req1 = MagicMock()
        req1.client.host = "10.0.0.1"
        req1.headers = {}
        req2 = MagicMock()
        req2.client.host = "10.0.0.2"
        req2.headers = {}
        limiter.check(req1)
        limiter.check(req2)  # Should not raise

    def test_x_forwarded_for_respected(self):
        """X-Forwarded-For header is used for IP extraction."""
        from fastapi import HTTPException

        limiter = InMemoryRateLimiter(cooldown_seconds=10.0)
        req1 = MagicMock()
        req1.client.host = "172.17.0.1"
        req1.headers = {"x-forwarded-for": "1.2.3.4, 172.17.0.1"}
        req2 = MagicMock()
        req2.client.host = "172.17.0.1"
        req2.headers = {"x-forwarded-for": "1.2.3.4, 172.17.0.1"}
        limiter.check(req1)
        with pytest.raises(HTTPException):
            limiter.check(req2)

    def test_cleanup_evicts_expired(self):
        """Cleanup removes entries older than max_age."""
        limiter = InMemoryRateLimiter(cooldown_seconds=10.0)
        # Manually insert an old entry
        limiter._last_request["old_ip"] = 0.0  # Very old timestamp
        limiter.cleanup(max_age=1.0)
        assert "old_ip" not in limiter._last_request
