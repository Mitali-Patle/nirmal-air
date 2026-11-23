"""Model providers: Groq and Google Gemini, both called over plain HTTPS with JSON output.

Each provider turns a request into the model's raw JSON text or raises a typed error the
chain knows how to handle. Error messages carry only status codes, never keys or content.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

import httpx
from pydantic import BaseModel

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
HTTP_TOO_MANY_REQUESTS = 429


class ProviderError(Exception):
    """The provider gave no usable answer (network, server, timeout or empty reply)."""


class RateLimitedError(ProviderError):
    """The provider's quota is used up for now.

    Attributes:
        retry_after_s: Seconds the provider asked us to wait, if it said.
    """

    def __init__(self, message: str, retry_after_s: float | None) -> None:
        super().__init__(message)
        self.retry_after_s = retry_after_s


@dataclass(frozen=True)
class LLMRequest:
    """One call to a model: a system prompt, one user message and the answer's schema."""

    system: str
    user: str
    schema: type[BaseModel]
    temperature: float
    max_output_tokens: int
    timeout_s: float


class Provider(Protocol):
    """Anything that answers an `LLMRequest` with JSON text."""

    @property
    def name(self) -> str:
        """Identifier such as `groq:openai/gpt-oss-120b`, shown in provenance."""
        ...

    async def generate(self, request: LLMRequest) -> str:
        """Return the model's raw JSON answer.

        Raises:
            ProviderError: When no usable answer came back.
        """
        ...


class _HttpProvider:
    """A model reached over HTTPS with an API key; subclasses build the request body."""

    vendor = ""

    def __init__(self, client: httpx.AsyncClient, model: str, api_key: str) -> None:
        self._client = client
        self._model = model
        self._api_key = api_key

    @property
    def name(self) -> str:
        """Vendor and model, for example `groq:openai/gpt-oss-120b`."""
        return f"{self.vendor}:{self._model}"

    async def _post(
        self, url: str, headers: dict[str, str], body: dict[str, Any], timeout_s: float
    ) -> Any:  # noqa: ANN401 - decoded JSON
        """POST a JSON body and return the decoded reply, mapping failures to our errors."""
        try:
            response = await self._client.post(url, headers=headers, json=body, timeout=timeout_s)
        except httpx.HTTPError as error:
            raise ProviderError(f"{self.name}: {type(error).__name__}") from error
        if response.status_code == HTTP_TOO_MANY_REQUESTS:
            raise RateLimitedError(f"{self.name}: rate limited", _retry_after(response))
        if response.is_error:
            raise ProviderError(f"{self.name}: HTTP {response.status_code}")
        try:
            return response.json()
        except ValueError as error:
            raise ProviderError(f"{self.name}: reply was not JSON") from error


class GroqProvider(_HttpProvider):
    """A Groq-hosted model through its OpenAI-compatible chat API."""

    vendor = "groq"

    async def generate(self, request: LLMRequest) -> str:
        """Return the model's JSON answer.

        Args:
            request: What to ask.

        Returns:
            The answer text.
        """
        body: dict[str, Any] = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": request.system},
                {"role": "user", "content": request.user},
            ],
            "temperature": request.temperature,
            "max_completion_tokens": request.max_output_tokens,
            # Non-strict schema mode: our own Pydantic validation is the strict check.
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": request.schema.__name__,
                    "schema": request.schema.model_json_schema(),
                },
            },
        }
        if "gpt-oss" in self._model:
            body["reasoning_effort"] = "low"
        headers = {"Authorization": f"Bearer {self._api_key}"}
        data = await self._post(GROQ_URL, headers, body, request.timeout_s)
        return _text(self.name, lambda: data["choices"][0]["message"]["content"])


class GeminiProvider(_HttpProvider):
    """A Gemini model through the Generative Language REST API."""

    vendor = "gemini"

    async def generate(self, request: LLMRequest) -> str:
        """Return the model's JSON answer.

        Args:
            request: What to ask.

        Returns:
            The answer text.
        """
        body = {
            "systemInstruction": {"parts": [{"text": request.system}]},
            "contents": [{"role": "user", "parts": [{"text": request.user}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseJsonSchema": request.schema.model_json_schema(),
                "temperature": request.temperature,
                "maxOutputTokens": request.max_output_tokens,
            },
        }
        url = GEMINI_URL.format(model=self._model)
        headers = {"x-goog-api-key": self._api_key}
        data = await self._post(url, headers, body, request.timeout_s)
        return _text(self.name, lambda: data["candidates"][0]["content"]["parts"][0]["text"])


def _text(name: str, extract: Callable[[], object]) -> str:
    """Pull the answer text out of a reply, or fail if it is missing or empty."""
    try:
        text = extract()
    except (KeyError, IndexError, TypeError) as error:
        raise ProviderError(f"{name}: unexpected reply shape") from error
    if not isinstance(text, str) or not text.strip():
        raise ProviderError(f"{name}: empty answer")
    return text


def _retry_after(response: httpx.Response) -> float | None:
    try:
        return float(response.headers["retry-after"])
    except (KeyError, ValueError):
        return None


# Preferred order: Groq answered a full plan in 2 to 3 s in testing; the Gemini models are
# backups with their own quotas (the second was slower, about 5 s).
GROQ_MODEL = "openai/gpt-oss-120b"
GEMINI_MODELS = ("gemini-3.5-flash-lite", "gemini-3.1-flash-lite")


def default_providers(
    client: httpx.AsyncClient, groq_key: str | None, gemini_key: str | None
) -> list[Provider]:
    """The models to try, in order, for whichever keys are configured.

    Args:
        client: Shared HTTP client.
        groq_key: Groq API key, if any.
        gemini_key: Gemini API key, if any.

    Returns:
        Providers in order of preference; empty when no key is set (standard advice only).
    """
    providers: list[Provider] = []
    if groq_key:
        providers.append(GroqProvider(client, GROQ_MODEL, groq_key))
    if gemini_key:
        providers += [GeminiProvider(client, model, gemini_key) for model in GEMINI_MODELS]
    return providers
