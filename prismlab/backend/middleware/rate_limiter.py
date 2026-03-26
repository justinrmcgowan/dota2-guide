"""Per-IP rate limiting for the recommend endpoint.

Prevents rapid-fire requests from the same client within a configurable
cooldown window. Uses monotonic time for drift-free intervals.
"""

import time

from fastapi import HTTPException, Request


class InMemoryRateLimiter:
    """Simple per-IP rate limiter with configurable cooldown.

    Tracks the last request timestamp per client IP using monotonic clock.
    Raises HTTP 429 with Retry-After header if the same IP requests again
    within the cooldown window.
    """

    def __init__(self, cooldown_seconds: float = 10.0) -> None:
        self.cooldown_seconds = cooldown_seconds
        self._last_request: dict[str, float] = {}

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP, preferring X-Forwarded-For for reverse proxy setups."""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            # First IP in chain is the real client
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def check(self, request: Request) -> None:
        """Check if the request is within the cooldown window.

        Raises HTTPException 429 with Retry-After header if rate limited.
        Updates the last request timestamp on success.
        """
        ip = self._get_client_ip(request)
        now = time.monotonic()
        last = self._last_request.get(ip)

        if last is not None:
            remaining = self.cooldown_seconds - (now - last)
            if remaining > 0:
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests. Try again shortly.",
                    headers={"Retry-After": str(int(remaining) + 1)},
                )

        self._last_request[ip] = now

    def cleanup(self, max_age: float = 300.0) -> None:
        """Evict entries older than max_age seconds."""
        now = time.monotonic()
        expired = [ip for ip, ts in self._last_request.items() if now - ts > max_age]
        for ip in expired:
            del self._last_request[ip]


# Module-level singleton
rate_limiter = InMemoryRateLimiter()


async def check_rate_limit(request: Request) -> None:
    """FastAPI dependency that enforces per-IP rate limiting."""
    rate_limiter.check(request)
