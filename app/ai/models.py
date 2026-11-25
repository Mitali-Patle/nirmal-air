"""Which models the app asks, in order, for the keys that are configured."""

import httpx

from app.ai.providers import GeminiProvider, GroqProvider, Provider

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
