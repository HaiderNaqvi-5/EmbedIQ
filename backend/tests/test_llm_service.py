"""Tests for the LLM service (app.services.llm_service)."""

import pytest

from app.services.llm_service import (
    BaseLLMProvider,
    MockLLMProvider,
    get_llm_provider,
)


# ---------------------------------------------------------------------------
# MockLLMProvider
# ---------------------------------------------------------------------------


class TestMockLLMProvider:
    @pytest.mark.asyncio
    async def test_complete_chat_returns_fixed_response(self):
        provider = MockLLMProvider()
        result = await provider.complete_chat(
            [{"role": "user", "content": "Hello"}],
            system="You are a bot.",
        )
        assert result == "This is a mock response from the bot."

    @pytest.mark.asyncio
    async def test_stream_chat_yields_fixed_response(self):
        provider = MockLLMProvider()
        tokens = []
        async for token in provider.stream_chat(
            [{"role": "user", "content": "Hello"}],
            system="You are a bot.",
        ):
            tokens.append(token)

        assert len(tokens) == 1
        assert tokens[0] == "This is a mock response from the bot."


# ---------------------------------------------------------------------------
# get_llm_provider factory
# ---------------------------------------------------------------------------


class TestGetLLMProvider:
    @pytest.mark.asyncio
    async def test_mock_provider_when_api_key_is_placeholder(self, monkeypatch):
        from app.core import config as config_mod

        monkeypatch.setattr(config_mod.settings, "LLM_API_KEY", "mock-key")
        monkeypatch.setattr(config_mod.settings, "LLM_PROVIDER", "openai")

        provider = get_llm_provider()
        assert isinstance(provider, MockLLMProvider)

    @pytest.mark.asyncio
    async def test_mock_provider_when_provider_not_openai(self, monkeypatch):
        from app.core import config as config_mod

        monkeypatch.setattr(config_mod.settings, "LLM_API_KEY", "sk-real-key-here")
        monkeypatch.setattr(config_mod.settings, "LLM_PROVIDER", "anthropic")

        provider = get_llm_provider()
        assert isinstance(provider, MockLLMProvider)
