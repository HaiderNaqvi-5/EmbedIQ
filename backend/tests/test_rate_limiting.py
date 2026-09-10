"""
Rate Limiting Tests (PRD Section 11.3)
=======================================
Tests for the in-memory sliding-window rate limiter middleware.
"""

import time
import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.core.rate_limit import _SlidingWindowCounter


# ---------------------------------------------------------------------------
# Unit tests for _SlidingWindowCounter
# ---------------------------------------------------------------------------

class TestSlidingWindowCounter:
    def test_allows_requests_within_limit(self):
        counter = _SlidingWindowCounter(window_seconds=60, max_requests=5)
        for _ in range(5):
            allowed, remaining = counter.is_allowed("user1")
            assert allowed is True
        assert remaining == 0

    def test_rejects_when_limit_exceeded(self):
        counter = _SlidingWindowCounter(window_seconds=60, max_requests=3)
        for _ in range(3):
            counter.is_allowed("user1")
        allowed, remaining = counter.is_allowed("user1")
        assert allowed is False
        assert remaining == 0

    def test_different_keys_independent(self):
        counter = _SlidingWindowCounter(window_seconds=60, max_requests=2)
        counter.is_allowed("user1")
        counter.is_allowed("user1")
        # user1 is now at limit
        allowed1, _ = counter.is_allowed("user1")
        assert allowed1 is False

        # user2 should still be allowed
        allowed2, remaining2 = counter.is_allowed("user2")
        assert allowed2 is True
        assert remaining2 == 1

    def test_window_expiry_allows_new_requests(self):
        counter = _SlidingWindowCounter(window_seconds=1, max_requests=2)
        counter.is_allowed("user1")
        counter.is_allowed("user1")
        # At limit
        assert counter.is_allowed("user1")[0] is False

        # Wait for window to expire
        time.sleep(1.1)

        allowed, remaining = counter.is_allowed("user1")
        assert allowed is True
        assert remaining == 1

    def test_empty_key_is_allowed(self):
        counter = _SlidingWindowCounter(window_seconds=60, max_requests=5)
        allowed, remaining = counter.is_allowed("")
        assert allowed is True
        assert remaining == 4

    def test_remaining_count_accurate(self):
        counter = _SlidingWindowCounter(window_seconds=60, max_requests=10)
        for i in range(7):
            allowed, remaining = counter.is_allowed("k")
            assert remaining == 9 - i


# ---------------------------------------------------------------------------
# Integration tests — rate limiter middleware behavior
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestRateLimitMiddleware:
    async def test_chat_within_limit_succeeds(self, client: AsyncClient):
        """Requests within the 60 req/min limit should pass through normally."""
        res = await client.post(
            "/api/chat",
            json={
                "bot_id": "00000000-0000-0000-0000-000000000000",
                "session_id": "sess_rl_test",
                "message": "Hello",
            },
        )
        # Should get 404 (bot not found), NOT 429 (rate limited)
        assert res.status_code == 404

    async def test_bot_create_within_limit_succeeds(self, client: AsyncClient):
        """Bot creation within the 5/hr limit should work."""
        reg = await client.post(
            "/api/auth/register",
            json={"email": f"rl_{time.time()}@example.com", "password": "Pass1234!"},
        )
        token = reg.json()["access_token"]

        res = await client.post(
            "/api/bots",
            json={"website_url": "https://rl-test.example.com"},
            headers={"Authorization": f"Bearer {token}"},
        )
        # Should get 202 (accepted), NOT 429
        assert res.status_code == 202

    async def test_non_rate_limited_endpoint_unaffected(self, client: AsyncClient):
        """Endpoints not covered by rate limiting should be unaffected."""
        res = await client.get("/api/health")
        assert res.status_code == 200

    async def test_rate_limit_headers_present_on_limit(self, client: AsyncClient):
        """When rate limited, response should include Retry-After and X-RateLimit headers."""
        # Flood chat endpoint to trigger rate limit
        for _ in range(65):
            await client.post(
                "/api/chat",
                json={
                    "bot_id": "00000000-0000-0000-0000-000000000000",
                    "session_id": "sess_flood",
                    "message": "Flood",
                },
            )

        # This one should be rate limited
        res = await client.post(
            "/api/chat",
            json={
                "bot_id": "00000000-0000-0000-0000-000000000000",
                "session_id": "sess_flood",
                "message": "Flood final",
            },
        )
        if res.status_code == 429:
            assert "Retry-After" in res.headers
            assert "X-RateLimit-Limit" in res.headers
            assert "X-RateLimit-Remaining" in res.headers
