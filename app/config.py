"""Application settings, loaded from environment variables (and `.env` in development)."""

from functools import lru_cache
from typing import Literal, Self

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

MIN_SESSION_SECRET_LENGTH = 32
# data.gov.in stalls requests that carry Python's default User-Agent (python-httpx,
# Python-urllib) until they time out, so every outside request names the app instead.
USER_AGENT = "NirmalAir/0.1"


class Settings(BaseSettings):
    """Runtime configuration.

    Secrets are `SecretStr` so they never appear in logs, reprs or error pages.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: Literal["development", "test", "production"] = "development"
    session_secret: SecretStr | None = None
    data_gov_api_key: SecretStr | None = None
    groq_api_key: SecretStr | None = None
    gemini_api_key: SecretStr | None = None

    @property
    def is_production(self) -> bool:
        """Whether the app is running in production."""
        return self.app_env == "production"

    @model_validator(mode="after")
    def require_production_secrets(self) -> Self:
        """Fail fast at startup when production is missing a required secret.

        Returns:
            The validated settings.

        Raises:
            ValueError: If a required production setting is missing or too weak.
        """
        if not self.is_production:
            return self
        if self.data_gov_api_key is None:
            raise ValueError("DATA_GOV_API_KEY is required in production")
        secret = self.session_secret.get_secret_value() if self.session_secret else ""
        if len(secret) < MIN_SESSION_SECRET_LENGTH:
            raise ValueError(
                f"SESSION_SECRET must be at least {MIN_SESSION_SECRET_LENGTH} characters"
            )
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings, loaded once.

    Returns:
        Settings read from the environment.
    """
    return Settings()
