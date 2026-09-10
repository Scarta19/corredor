"""Application settings, loaded from the environment.

Every deployment (local, staging, production) differs only by environment
variables; there are no environment-specific code paths.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn, SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["local", "test", "staging", "production"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    # --- Application ---
    environment: Environment = "local"
    debug: bool = False
    project_name: str = "Corredor"
    api_v1_prefix: str = "/api/v1"

    # --- Security ---
    secret_key: SecretStr = SecretStr("change-me-in-every-real-deployment")
    access_token_ttl_minutes: int = 60 * 12
    jwt_algorithm: str = "HS256"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # --- Persistence ---
    database_url: PostgresDsn = PostgresDsn(
        "postgresql+asyncpg://corredor:corredor@localhost:5432/corredor"
    )
    database_echo: bool = False
    database_pool_size: int = 10
    database_max_overflow: int = 5

    redis_url: RedisDsn = RedisDsn("redis://localhost:6379/0")

    # --- Renewal engine ---
    # Days before expiry at which a renewal action is generated. Ordered
    # descending; each threshold produces exactly one task per policy.
    renewal_thresholds_days: list[int] = Field(default_factory=lambda: [60, 30, 15, 7])
    renewal_sweep_hour_utc: int = 6

    # --- Intelligence layer ---
    anthropic_api_key: SecretStr | None = None
    anthropic_model: str = "claude-sonnet-5"
    enable_ai_triage: bool = False

    # --- WhatsApp (Módulo 3, phase 2) ---
    whatsapp_verify_token: SecretStr | None = None
    whatsapp_access_token: SecretStr | None = None
    whatsapp_phone_number_id: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Settings are read once per process and cached."""
    return Settings()
