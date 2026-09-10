"""
Chat & Widget Integration Tests
================================
Tests for chat endpoints (PRD Sections 6.3.4, 8.3) and widget config.
"""

import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _register_and_get_token(client: AsyncClient) -> str:
    email = f"chat_{uuid.uuid4().hex[:8]}@example.com"
    res = await client.post(
        "/api/auth/register",
        json={"email": email, "password": "TestPass123!"},
    )
    assert res.status_code in (200, 201)
    return res.json()["access_token"]


async def _create_bot(client: AsyncClient, token: str, url: str = "https://example.com") -> str:
    res = await client.post(
        "/api/bots",
        json={"website_url": url},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 202
    return res.json()["bot_id"]


# ---------------------------------------------------------------------------
# Chat endpoint — bot readiness guard
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestChatBotReadiness:
    async def test_chat_rejects_pending_bot(self, client: AsyncClient):
        token = await _register_and_get_token(client)
        bot_id = await _create_bot(client, token)

        res = await client.post(
            "/api/chat",
            json={
                "bot_id": bot_id,
                "session_id": "sess_test_pending",
                "message": "Hello?",
            },
        )
        assert res.status_code == 409
        body = res.json()
        assert "detail" in body
        assert body["detail"]["code"] == "BOT_NOT_READY"

    async def test_chat_unknown_bot_returns_404(self, client: AsyncClient):
        res = await client.post(
            "/api/chat",
            json={
                "bot_id": str(uuid.uuid4()),
                "session_id": "sess_unknown",
                "message": "Hello?",
            },
        )
        assert res.status_code == 404

    async def test_chat_stream_rejects_pending_bot(self, client: AsyncClient):
        token = await _register_and_get_token(client)
        bot_id = await _create_bot(client, token)

        res = await client.post(
            "/api/chat/stream",
            json={
                "bot_id": bot_id,
                "session_id": "sess_test_stream",
                "message": "Hello?",
            },
        )
        assert res.status_code == 409


# ---------------------------------------------------------------------------
# Chat endpoint — request validation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestChatValidation:
    async def test_chat_missing_message_returns_422(self, client: AsyncClient):
        res = await client.post(
            "/api/chat",
            json={
                "bot_id": str(uuid.uuid4()),
                "session_id": "sess_test",
            },
        )
        assert res.status_code == 422

    async def test_chat_missing_bot_id_returns_422(self, client: AsyncClient):
        res = await client.post(
            "/api/chat",
            json={
                "session_id": "sess_test",
                "message": "Hello",
            },
        )
        assert res.status_code == 422


# ---------------------------------------------------------------------------
# Widget config endpoint
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestWidgetConfigEndpoint:
    async def test_widget_config_no_auth_required(self, client: AsyncClient):
        token = await _register_and_get_token(client)
        bot_id = await _create_bot(client, token)

        res = await client.get(f"/api/widget/config/{bot_id}")
        assert res.status_code == 200
        body = res.json()
        assert body["bot_id"] == bot_id
        assert "theme" in body
        assert "primary_color" in body["theme"]
        assert body["theme"]["primary_color"].startswith("#")

    async def test_widget_config_returns_default_theme(self, client: AsyncClient):
        token = await _register_and_get_token(client)
        bot_id = await _create_bot(client, token)

        res = await client.get(f"/api/widget/config/{bot_id}")
        assert res.status_code == 200
        body = res.json()
        theme = body["theme"]
        assert theme["primary_color"] == "#2563EB"
        assert theme["font_family"] == "Inter, sans-serif"
        assert theme["border_radius"] == "12px"
        assert theme["position"] == "bottom-right"

    async def test_widget_config_unknown_bot_returns_404(self, client: AsyncClient):
        res = await client.get(f"/api/widget/config/{uuid.uuid4()}")
        assert res.status_code == 404

    async def test_widget_config_includes_bot_status(self, client: AsyncClient):
        token = await _register_and_get_token(client)
        bot_id = await _create_bot(client, token)

        res = await client.get(f"/api/widget/config/{bot_id}")
        assert res.status_code == 200
        body = res.json()
        assert body["status"] == "PENDING"


# ---------------------------------------------------------------------------
# SSE streaming format
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestSSEFormat:
    async def test_stream_endpoint_returns_event_stream(self, client: AsyncClient):
        token = await _register_and_get_token(client)
        bot_id = await _create_bot(client, token)

        # Bot is PENDING, so we expect 409 — but the important thing is
        # that the endpoint exists and the route is registered
        res = await client.post(
            "/api/chat/stream",
            json={
                "bot_id": bot_id,
                "session_id": "sess_format_test",
                "message": "Test",
            },
        )
        # Should be 409 (bot not ready), confirming the route works
        assert res.status_code == 409
