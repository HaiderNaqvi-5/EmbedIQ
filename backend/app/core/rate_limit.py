"""
In-Memory Rate Limiter (PRD Section 11.3)
==========================================
Lightweight sliding-window rate limiter using an in-memory dict with TTL eviction.
No external dependencies required (no Redis needed for MVP).

Limits:
  - POST /api/chat and POST /api/chat/stream: 60 requests/minute per IP.
  - POST /api/bots: 5 requests/hour per authenticated user.
"""

import time
from collections import defaultdict
from typing import Dict, Tuple

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


class _SlidingWindowCounter:
    """Per-key sliding window rate counter.

    Stores (timestamp, count) tuples and evicts entries older than the window.
    """

    def __init__(self, window_seconds: int, max_requests: int):
        self.window_seconds = window_seconds
        self.max_requests = max_requests
        self._buckets: Dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str) -> Tuple[bool, int]:
        """Check if *key* is within the rate limit.

        Returns:
            (allowed, remaining) — remaining is the number of requests left
            in the current window (0 if exceeded).
        """
        now = time.monotonic()
        cutoff = now - self.window_seconds

        # Evict expired timestamps
        timestamps = self._buckets[key]
        self._buckets[key] = [t for t in timestamps if t > cutoff]

        if len(self._buckets[key]) >= self.max_requests:
            return False, 0

        self._buckets[key].append(now)
        remaining = self.max_requests - len(self._buckets[key])
        return True, remaining


# ---------------------------------------------------------------------------
# Global rate limiters (one per policy)
# ---------------------------------------------------------------------------

_chat_limiter = _SlidingWindowCounter(window_seconds=60, max_requests=60)
_bot_create_limiter = _SlidingWindowCounter(window_seconds=3600, max_requests=5)


def _client_ip(request: Request) -> str:
    """Extract the client IP from X-Forwarded-For or direct connection."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """ASGI middleware that enforces per-route rate limits.

    Applies:
      - 60 req/min per IP on POST /api/chat and POST /api/chat/stream
      - 5 req/hr per user on POST /api/bots (keyed on user ID from JWT)
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        path = request.url.path
        method = request.method.upper()

        # ── Chat rate limit (per IP) ──────────────────────────────────────
        if method == "POST" and path in ("/api/chat", "/api/chat/stream"):
            key = f"chat:{_client_ip(request)}"
            allowed, remaining = _chat_limiter.is_allowed(key)
            if not allowed:
                return Response(
                    content='{"error":{"code":"RATE_LIMITED","message":"Too many requests. Please try again later."}}',
                    status_code=429,
                    media_type="application/json",
                    headers={
                        "Retry-After": "60",
                        "X-RateLimit-Limit": "60",
                        "X-RateLimit-Remaining": "0",
                    },
                )

        # ── Bot creation rate limit (per user) ────────────────────────────
        if method == "POST" and path == "/api/bots":
            # Extract user ID from JWT if present
            user_key = self._extract_user_key(request)
            if user_key:
                key = f"bot_create:{user_key}"
                allowed, remaining = _bot_create_limiter.is_allowed(key)
                if not allowed:
                    return Response(
                        content='{"error":{"code":"RATE_LIMITED","message":"Bot creation limit reached. Please try again later."}}',
                        status_code=429,
                        media_type="application/json",
                        headers={
                            "Retry-After": "3600",
                            "X-RateLimit-Limit": "5",
                            "X-RateLimit-Remaining": "0",
                        },
                    )

        return await call_next(request)

    def _extract_user_key(self, request: Request) -> str | None:
        """Try to extract user identifier from the Authorization header JWT."""
        auth = request.headers.get("authorization", "")
        if not auth.startswith("Bearer "):
            return None
        token = auth[7:]
        try:
            from app.core.security import decode_access_token
            payload = decode_access_token(token)
            if payload:
                return payload.get("sub", _client_ip(request))
        except Exception:
            pass
        return _client_ip(request)
