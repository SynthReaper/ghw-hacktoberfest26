"""Configuration and environment settings for Open-Switch."""

from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with runtime mode constraints and spend caps."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Runtime mode
    openswitch_mode: Literal["hosted", "local"] = Field(
        default="hosted",
        description="Hosted mode allows remote providers; local mode restricts to localhost.",
    )
    demo_mode: bool = Field(
        default=False,
        description="Demo mode limits upload rows, visitor runs, and enables 24h cleanup.",
    )

    # Safety limits and caps
    max_rows: int = Field(default=200, ge=10, le=5000)
    max_upload_mb: int = Field(default=2, ge=1, le=50)
    max_concurrent_experiments: int = Field(default=2, ge=1, le=10)
    max_experiments_per_visitor_day: int = Field(default=3, ge=1, le=100)
    experiment_max_cost_usd: float = Field(default=2.0, ge=0.1, le=50.0)
    global_daily_budget_usd: float = Field(default=5.0, ge=0.5, le=100.0)
    kill_switch: bool = Field(default=False, description="Emergency stop for all evaluation runs.")

    # Storage paths
    data_dir: Path = Field(default=Path("./data_storage"))
    database_url: str = Field(
        default="sqlite+aiosqlite:///data_storage/openswitch.db",
        description="Async SQLAlchemy database connection string.",
    )

    # Observability & Partner Keys
    sentry_dsn: str | None = None
    do_model_access_key: str | None = None
    backboard_api_key: str | None = None
    tinker_api_key: str | None = None
    elevenlabs_api_key: str | None = None
    baseline_api_key: str | None = None

    @field_validator("data_dir", mode="after")
    @classmethod
    def ensure_data_dir(cls, v: Path) -> Path:
        v.mkdir(parents=True, exist_ok=True)
        return v

    def validate_provider_url(self, base_url: str, provider_name: str = "custom") -> None:
        """Validate whether a provider URL is permitted in the current OPENSWITCH_MODE.

        In local mode (OPENSWITCH_MODE=local), only localhost, 127.0.0.1, and [::1] are allowed.
        """
        if self.openswitch_mode != "local":
            return

        parsed = urlparse(base_url)
        hostname = (parsed.hostname or "").lower()
        allowed_hosts = {"localhost", "127.0.0.1", "::1"}

        if hostname not in allowed_hosts:
            raise PermissionError(
                f"OPENSWITCH_MODE=local is active: Provider '{provider_name}' attempted to access "
                f"external host '{hostname}' at URL '{base_url}'. In local mode, only localhost "
                f"(e.g., http://localhost:11434/v1) is permitted to prevent accidental data egress."
            )

    def get_required_key(self, key_name: str, provider_name: str) -> str:
        """Fetch a required API key or raise an actionable error."""
        val = getattr(self, key_name.lower(), None)
        if not val or not str(val).strip():
            env_var = key_name.upper()
            raise ValueError(
                f"Missing required API key for provider '{provider_name}'. "
                f"Please define {env_var} in your .env file or environment variables."
            )
        return str(val).strip()


# Global settings singleton
settings = Settings()
