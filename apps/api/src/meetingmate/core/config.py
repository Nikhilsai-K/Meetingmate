"""Typed application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )

    environment: str = Field(default="development", alias="NODE_ENV")
    log_level: str = Field(default="info", alias="LOG_LEVEL")

    database_url: str = Field(alias="DATABASE_URL")
    redis_url: str = Field(alias="REDIS_URL")
    qdrant_url: str = Field(alias="QDRANT_URL")
    qdrant_api_key: str | None = Field(default=None, alias="QDRANT_API_KEY")

    s3_endpoint_url: str | None = Field(default=None, alias="S3_ENDPOINT_URL")
    s3_region: str = Field(default="ap-northeast-1", alias="S3_REGION")
    s3_bucket_transcripts: str = Field(alias="S3_BUCKET_TRANSCRIPTS")
    s3_access_key_id: str = Field(alias="S3_ACCESS_KEY_ID")
    s3_secret_access_key: str = Field(alias="S3_SECRET_ACCESS_KEY")

    clerk_secret_key: str = Field(alias="CLERK_SECRET_KEY")
    clerk_jwks_url: str = Field(alias="CLERK_JWKS_URL")
    clerk_issuer: str = Field(alias="CLERK_ISSUER")

    anthropic_api_key: str = Field(alias="ANTHROPIC_API_KEY")
    deepgram_api_key: str = Field(alias="DEEPGRAM_API_KEY")
    voyage_api_key: str = Field(alias="VOYAGE_API_KEY")
    cohere_api_key: str = Field(alias="COHERE_API_KEY")
    azure_speech_key: str | None = Field(default=None, alias="AZURE_SPEECH_KEY")
    azure_speech_region: str | None = Field(default=None, alias="AZURE_SPEECH_REGION")

    langfuse_public_key: str | None = Field(default=None, alias="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: str | None = Field(default=None, alias="LANGFUSE_SECRET_KEY")
    langfuse_host: str | None = Field(default=None, alias="LANGFUSE_HOST")
    sentry_dsn: str | None = Field(default=None, alias="SENTRY_DSN")

    stripe_secret_key: str | None = Field(default=None, alias="STRIPE_SECRET_KEY")
    stripe_webhook_secret: str | None = Field(default=None, alias="STRIPE_WEBHOOK_SECRET")
    stripe_price_pro_monthly: str | None = Field(default=None, alias="STRIPE_PRICE_PRO_MONTHLY")
    stripe_price_team_monthly: str | None = Field(default=None, alias="STRIPE_PRICE_TEAM_MONTHLY")

    todoist_client_id: str | None = Field(default=None, alias="TODOIST_CLIENT_ID")
    todoist_client_secret: str | None = Field(default=None, alias="TODOIST_CLIENT_SECRET")
    notion_client_id: str | None = Field(default=None, alias="NOTION_CLIENT_ID")
    notion_client_secret: str | None = Field(default=None, alias="NOTION_CLIENT_SECRET")
    google_client_id: str | None = Field(default=None, alias="GOOGLE_CLIENT_ID")
    google_client_secret: str | None = Field(default=None, alias="GOOGLE_CLIENT_SECRET")

    api_base_url: str = Field(default="http://localhost:8000", alias="API_BASE_URL")
    web_base_url: str = Field(default="http://localhost:3000", alias="WEB_BASE_URL")

    integration_credential_aes_key: str = Field(
        default="0123456789abcdef0123456789abcdef", alias="INTEGRATION_CREDENTIAL_AES_KEY"
    )
    rate_limit_free_meeting_hours_per_day: int = Field(
        default=5, alias="RATE_LIMIT_FREE_MEETING_HOURS_PER_DAY"
    )
    rate_limit_pro_meeting_hours_per_day: int = Field(
        default=24, alias="RATE_LIMIT_PRO_MEETING_HOURS_PER_DAY"
    )

    allowed_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "https://meetingmate.app",
            # chrome-extension://... origins are handled specifically per-request; see middleware.
        ]
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
