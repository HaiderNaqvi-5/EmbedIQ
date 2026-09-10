"""
Provider-Abstracted LLM Service
===============================
Supported providers:
- OpenAI
- Groq with multi-key failover
- Mock provider
Groq failover behavior:
- 401/403: skip bad/unauthorized key
- 429: respect Retry-After, then fail over
- 5xx/network errors: retry and then fail over
- other 4xx: fail immediately because another key is unlikely to fix the request
"""
import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, List
import httpx
from app.core.config import settings
logger = logging.getLogger("embediq.llm")
_OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
_GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
_LLM_TIMEOUT = 60.0
_MOCK_KEYS = {
    "",
    "mock-key",
    "mock-key-for-development",
}
class BaseLLMProvider(ABC):
    @abstractmethod
    async def stream_chat(
        self,
        messages: List[Dict],
        system: str,
    ) -> AsyncGenerator[str, None]:
        ...
        yield  # type: ignore[misc]
    @abstractmethod
    async def complete_chat(
        self,
        messages: List[Dict],
        system: str,
    ) -> str:
        ...
# ============================================================
# OpenAI
# ============================================================
class OpenAILLMProvider(BaseLLMProvider):
    def _build_payload(
        self,
        messages: List[Dict],
        system: str,
        stream: bool,
    ) -> Dict:
        full_messages = [
            {
                "role": "system",
                "content": system,
            }
        ] + messages
        return {
            "model": settings.LLM_MODEL,
            "messages": full_messages,
            "stream": stream,
            "max_completion_tokens": 1024,
        }
    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {settings.LLM_API_KEY}",
            "Content-Type": "application/json",
        }
    async def stream_chat(
        self,
        messages: List[Dict],
        system: str,
    ) -> AsyncGenerator[str, None]:
        payload = self._build_payload(
            messages,
            system,
            stream=True,
        )
        async with httpx.AsyncClient(
            timeout=_LLM_TIMEOUT
        ) as client:
            async with client.stream(
                "POST",
                _OPENAI_CHAT_URL,
                headers=self._headers(),
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    raw = line[len("data: "):].strip()
                    if raw == "[DONE]":
                        break
                    try:
                        data = json.loads(raw)
                        content = (
                            data.get("choices", [{}])[0]
                            .get("delta", {})
                            .get("content", "")
                        )
                        if content:
                            yield content
                    except (
                        json.JSONDecodeError,
                        IndexError,
                        KeyError,
                    ):
                        continue
    async def complete_chat(
        self,
        messages: List[Dict],
        system: str,
    ) -> str:
        payload = self._build_payload(
            messages,
            system,
            stream=False,
        )
        async with httpx.AsyncClient(
            timeout=_LLM_TIMEOUT
        ) as client:
            response = await client.post(
                _OPENAI_CHAT_URL,
                headers=self._headers(),
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
# ============================================================
# Groq
# ============================================================
class GroqLLMProvider(BaseLLMProvider):
    def __init__(self):
        self.api_keys = [
            key
            for key in [
                settings.GROQ_API_KEY_1,
                settings.GROQ_API_KEY_2,
                settings.GROQ_API_KEY_3,
            ]
            if key and key not in _MOCK_KEYS
        ]
        if not self.api_keys:
            raise RuntimeError(
                "LLM_PROVIDER=groq but no valid Groq API keys are configured."
            )
    def _build_payload(
        self,
        messages: List[Dict],
        system: str,
        stream: bool,
    ) -> Dict:
        full_messages = [
            {
                "role": "system",
                "content": system,
            }
        ] + messages
        return {
            "model": settings.LLM_MODEL,
            "messages": full_messages,
            "stream": stream,
            "max_completion_tokens": 1024,
        }
    @staticmethod
    def _headers(api_key: str) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
    @staticmethod
    def _retry_after(response: httpx.Response) -> float:
        raw = response.headers.get("retry-after")
        if not raw:
            return 1.0
        try:
            return max(float(raw), 0.0)
        except ValueError:
            return 1.0
    async def complete_chat(
        self,
        messages: List[Dict],
        system: str,
    ) -> str:
        payload = self._build_payload(
            messages,
            system,
            stream=False,
        )
        retries = max(
            1,
            settings.LLM_RETRIES_PER_KEY,
        )
        last_error: Exception | None = None
        async with httpx.AsyncClient(
            timeout=_LLM_TIMEOUT
        ) as client:
            for key_index, api_key in enumerate(
                self.api_keys,
                start=1,
            ):
                for attempt in range(
                    1,
                    retries + 1,
                ):
                    try:
                        response = await client.post(
                            _GROQ_CHAT_URL,
                            headers=self._headers(api_key),
                            json=payload,
                        )
                        # Invalid / unauthorized credential
                        if response.status_code in {
                            401,
                            403,
                        }:
                            logger.warning(
                                "Groq key %d rejected with HTTP %d. "
                                "Trying next key.",
                                key_index,
                                response.status_code,
                            )
                            last_error = RuntimeError(
                                f"Groq credential {key_index} rejected"
                            )
                            break
                        # Rate limit
                        if response.status_code == 429:
                            retry_after = self._retry_after(
                                response
                            )
                            logger.warning(
                                "Groq key %d rate limited. "
                                "Retry-After=%.2fs.",
                                key_index,
                                retry_after,
                            )
                            last_error = RuntimeError(
                                f"Groq key {key_index} rate limited"
                            )
                            # Retry this key when another attempt remains.
                            if attempt < retries:
                                await asyncio.sleep(
                                    retry_after
                                )
                                continue
                            # Otherwise fail over.
                            break
                        # Server-side errors
                        if 500 <= response.status_code <= 599:
                            response_error = (
                                f"Groq server error "
                                f"HTTP {response.status_code}"
                            )
                            last_error = RuntimeError(
                                response_error
                            )
                            logger.warning(
                                "Groq key %d attempt %d/%d: %s",
                                key_index,
                                attempt,
                                retries,
                                response_error,
                            )
                            if attempt < retries:
                                await asyncio.sleep(
                                    2 ** (attempt - 1)
                                )
                                continue
                            break
                        # Other client errors such as malformed payload/model.
                        # Changing credentials won't fix these.
                        if 400 <= response.status_code <= 499:
                            try:
                                error_body = response.json()
                            except Exception:
                                error_body = response.text
                            raise RuntimeError(
                                f"Groq request rejected "
                                f"(HTTP {response.status_code}): "
                                f"{error_body}"
                            )
                        response.raise_for_status()
                        data = response.json()
                        return (
                            data["choices"][0]
                            ["message"]
                            ["content"]
                        )
                    except (
                        httpx.TimeoutException,
                        httpx.NetworkError,
                    ) as exc:
                        last_error = exc
                        logger.warning(
                            "Groq key %d network failure "
                            "attempt %d/%d: %s",
                            key_index,
                            attempt,
                            retries,
                            exc,
                        )
                        if attempt < retries:
                            await asyncio.sleep(
                                2 ** (attempt - 1)
                            )
                            continue
                        break
        raise RuntimeError(
            "All configured Groq API keys failed."
        ) from last_error
    async def stream_chat(
        self,
        messages: List[Dict],
        system: str,
    ) -> AsyncGenerator[str, None]:
        # Important:
        # Failover must happen before streaming starts.
        # Once tokens have been sent to the user, switching providers/keys
        # could duplicate the beginning of the answer.
        payload = self._build_payload(
            messages,
            system,
            stream=True,
        )
        last_error: Exception | None = None
        started = False
        for key_index, api_key in enumerate(
            self.api_keys,
            start=1,
        ):
            try:
                async with httpx.AsyncClient(
                    timeout=_LLM_TIMEOUT
                ) as client:
                    async with client.stream(
                        "POST",
                        _GROQ_CHAT_URL,
                        headers=self._headers(api_key),
                        json=payload,
                    ) as response:
                        if response.status_code in {
                            401,
                            403,
                            429,
                        }:
                            logger.warning(
                                "Groq streaming key %d failed "
                                "with HTTP %d. Trying next key.",
                                key_index,
                                response.status_code,
                            )
                            last_error = RuntimeError(
                                f"Groq streaming key {key_index} "
                                f"failed HTTP {response.status_code}"
                            )
                            continue
                        if 500 <= response.status_code <= 599:
                            logger.warning(
                                "Groq streaming key %d server "
                                "failure HTTP %d.",
                                key_index,
                                response.status_code,
                            )
                            last_error = RuntimeError(
                                f"Groq server error "
                                f"HTTP {response.status_code}"
                            )
                            continue
                        response.raise_for_status()
                        started = False
                        async for line in response.aiter_lines():
                            if not line.startswith("data: "):
                                continue
                            raw = line[len("data: "):].strip()
                            if raw == "[DONE]":
                                return
                            try:
                                data = json.loads(raw)
                                content = (
                                    data.get(
                                        "choices",
                                        [{}],
                                    )[0]
                                    .get(
                                        "delta",
                                        {},
                                    )
                                    .get(
                                        "content",
                                        "",
                                    )
                                )
                                if content:
                                    started = True
                                    yield content
                            except (
                                json.JSONDecodeError,
                                IndexError,
                                KeyError,
                            ):
                                continue
                        # Successful stream finished normally.
                        return
            except (
                httpx.TimeoutException,
                httpx.NetworkError,
            ) as exc:
                last_error = exc
                logger.warning(
                    "Groq streaming key %d network error: %s",
                    key_index,
                    exc,
                )

                # Once any token has reached the client, failover would risk
                # duplicating the beginning of the answer.
                if started:
                    raise RuntimeError(
                        "Groq stream interrupted after response streaming began."
                    ) from exc

                # No token was emitted, so trying the next credential is safe.
                continue
            except httpx.HTTPStatusError as exc:
                last_error = exc
                # Don't hide malformed request/model errors.
                if 400 <= exc.response.status_code < 500:
                    raise
                continue
        # Distinguish quota/rate-limit exhaustion from other provider failures.
        if last_error is not None and "429" in str(last_error):
            raise RuntimeError("LLM_RATE_LIMIT") from last_error

        raise RuntimeError(
            "All configured Groq API keys failed for streaming."
        ) from last_error
# ============================================================
# Mock
# ============================================================
class MockLLMProvider(BaseLLMProvider):
    async def stream_chat(
        self,
        messages: List[Dict],
        system: str,
    ) -> AsyncGenerator[str, None]:
        yield "This is a mock response from the bot."
    async def complete_chat(
        self,
        messages: List[Dict],
        system: str,
    ) -> str:
        return "This is a mock response from the bot."
# ============================================================
# Provider factory
# ============================================================
def get_llm_provider() -> BaseLLMProvider:
    provider = settings.LLM_PROVIDER.lower()
    if (
        provider == "openai"
        and settings.LLM_API_KEY not in _MOCK_KEYS
    ):
        logger.debug(
            "LLM provider: OpenAI (model=%s)",
            settings.LLM_MODEL,
        )
        return OpenAILLMProvider()
    if provider == "groq":
        logger.debug(
            "LLM provider: Groq "
            "(model=%s, failover enabled)",
            settings.LLM_MODEL,
        )
        return GroqLLMProvider()
    logger.debug(
        "LLM provider: Mock"
    )
    return MockLLMProvider()