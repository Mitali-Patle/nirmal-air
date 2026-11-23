import json

import httpx
import pytest
import respx
from pydantic import BaseModel

from app.ai.providers import (
    GEMINI_URL,
    GROQ_URL,
    GeminiProvider,
    GroqProvider,
    LLMRequest,
    ProviderError,
    RateLimitedError,
    default_providers,
)


class Reply(BaseModel):
    text: str


REQUEST = LLMRequest("system", "user", Reply, 0.3, 200, 5.0)
GEMINI = GEMINI_URL.format(model="gemini-3.5-flash-lite")


def groq_reply(content: object) -> dict[str, object]:
    return {"choices": [{"message": {"content": content}}]}


def gemini_reply(text: object) -> dict[str, object]:
    return {"candidates": [{"content": {"parts": [{"text": text}]}}]}


@respx.mock
async def test_groq_sends_the_schema_and_returns_the_text(client: httpx.AsyncClient) -> None:
    route = respx.post(GROQ_URL).respond(json=groq_reply('{"text": "hi"}'))
    provider = GroqProvider(client, "openai/gpt-oss-120b", "test-key")
    assert await provider.generate(REQUEST) == '{"text": "hi"}'
    body = json.loads(route.calls.last.request.content)
    assert body["response_format"]["json_schema"]["name"] == "Reply"
    assert body["reasoning_effort"] == "low"
    assert route.calls.last.request.headers["authorization"] == "Bearer test-key"
    assert provider.name == "groq:openai/gpt-oss-120b"


@respx.mock
async def test_gemini_sends_the_schema_and_returns_the_text(client: httpx.AsyncClient) -> None:
    route = respx.post(GEMINI).respond(json=gemini_reply('{"text": "hi"}'))
    provider = GeminiProvider(client, "gemini-3.5-flash-lite", "test-key")
    assert await provider.generate(REQUEST) == '{"text": "hi"}'
    body = json.loads(route.calls.last.request.content)
    assert body["generationConfig"]["responseJsonSchema"]["title"] == "Reply"
    assert route.calls.last.request.headers["x-goog-api-key"] == "test-key"


@respx.mock
async def test_a_429_says_when_to_retry(client: httpx.AsyncClient) -> None:
    respx.post(GROQ_URL).respond(429, headers={"retry-after": "12"})
    with pytest.raises(RateLimitedError) as caught:
        await GroqProvider(client, "llama", "key").generate(REQUEST)
    assert caught.value.retry_after_s == 12


@respx.mock
async def test_a_429_without_a_delay(client: httpx.AsyncClient) -> None:
    respx.post(GEMINI).respond(429)
    with pytest.raises(RateLimitedError) as caught:
        await GeminiProvider(client, "gemini-3.5-flash-lite", "key").generate(REQUEST)
    assert caught.value.retry_after_s is None


@respx.mock
@pytest.mark.parametrize(
    ("response", "message"),
    [
        (httpx.Response(503), "HTTP 503"),
        (httpx.Response(200, text="<html>"), "not JSON"),
        (httpx.Response(200, json={"choices": []}), "unexpected reply shape"),
        (httpx.Response(200, json=groq_reply("  ")), "empty answer"),
        (httpx.Response(200, json=groq_reply(None)), "empty answer"),
    ],
)
async def test_unusable_replies_raise(
    client: httpx.AsyncClient, response: httpx.Response, message: str
) -> None:
    respx.post(GROQ_URL).mock(return_value=response)
    with pytest.raises(ProviderError, match=message):
        await GroqProvider(client, "llama", "key").generate(REQUEST)


@respx.mock
async def test_network_failures_raise_without_details(client: httpx.AsyncClient) -> None:
    respx.post(GEMINI).mock(side_effect=httpx.ReadTimeout("slow"))
    with pytest.raises(ProviderError, match="ReadTimeout") as caught:
        await GeminiProvider(client, "gemini-3.5-flash-lite", "secret").generate(REQUEST)
    assert "secret" not in str(caught.value)


async def test_models_are_tried_in_order_for_the_keys_configured(client: httpx.AsyncClient) -> None:
    assert default_providers(client, None, None) == []
    assert [provider.name for provider in default_providers(client, "groq", "gemini")] == [
        "groq:openai/gpt-oss-120b",
        "gemini:gemini-3.5-flash-lite",
        "gemini:gemini-3.1-flash-lite",
    ]
    assert len(default_providers(client, None, "gemini")) == 2
