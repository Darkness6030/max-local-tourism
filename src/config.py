from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, HttpUrl, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.constants import OVERPASS_API_URL

ROOT_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    app_name: str = "MAX.Локальный Туризм API"
    app_version: str = "0.3.0"
    app_env: Literal["development", "test", "production"] = "development"
    app_log_level: str = "INFO"
    app_root_path: str = Field(default="", pattern=r"^(?:/[a-zA-Z0-9_-]+)*$")
    database_url: SecretStr | None = None

    max_bot_token: SecretStr | None = None
    max_webhook_secret: SecretStr | None = None
    max_bot_username: str | None = None
    max_ca_bundle_file: str | None = None
    max_allow_local_auth: bool = False
    max_local_client_hosts: list[str] = Field(
        default_factory=lambda: ["127.0.0.1", "::1"]
    )
    max_init_data_ttl_seconds: int = Field(default=3600, ge=60, le=86400)
    max_job_concurrency: int = Field(default=3, ge=1, le=20)

    yandex_schedule_api_key: SecretStr | None = None
    gigachat_credentials: SecretStr | None = None
    gigachat_scope: str = "GIGACHAT_API_CORP"
    gigachat_model: str = "GigaChat-2-Max"
    gigachat_timeout_seconds: float = Field(default=90, gt=0, le=300)
    gigachat_verify_ssl_certs: bool = True
    gigachat_ca_bundle_file: str | None = None

    weather_provider: Literal["auto", "open-meteo", "openweather"] = "auto"
    openweather_api_key: SecretStr | None = None

    http_timeout_seconds: float = Field(default=20, gt=0, le=120)
    overpass_api_url: HttpUrl = Field(default=OVERPASS_API_URL, validate_default=True)
    nominatim_domain: str = "nominatim.openstreetmap.org"
    nominatim_user_agent: str = "max-local-tourism-mvp/0.1"

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_production(self) -> "Settings":
        if self.app_env == "production":
            if self.max_allow_local_auth:
                raise ValueError("Production запрещает MAX_ALLOW_LOCAL_AUTH")
            if not self.max_bot_token:
                raise ValueError("Production требует MAX_BOT_TOKEN")
            if self.gigachat_credentials and not self.gigachat_verify_ssl_certs:
                raise ValueError("Production требует проверку сертификата сервиса ИИ")
        return self

    @property
    def selected_weather_provider(self) -> Literal["open-meteo", "openweather"]:
        if self.weather_provider == "openweather":
            return "openweather"
        if self.weather_provider == "open-meteo":
            return "open-meteo"
        return "openweather" if self.openweather_api_key else "open-meteo"


@lru_cache
def get_settings() -> Settings:
    return Settings()
