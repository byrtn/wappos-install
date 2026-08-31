# Auteur : Patrick Ritaine

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="WAPPOS_API_", env_file=".env")

    portalapi_base_url: str = "http://127.0.0.1:6788"

    yunohost_api_base_url: str = "http://127.0.0.1:6787"

    upstream_timeout_seconds: float = 10.0

    log_level: str = "INFO"


settings = Settings()
