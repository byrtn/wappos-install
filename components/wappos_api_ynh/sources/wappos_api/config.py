# Auteur : Patrick Ritaine

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="WAPPOS_API_", env_file=".env")

    portalapi_base_url: str = "http://127.0.0.1:6788"

    yunohost_api_base_url: str = "http://127.0.0.1:6787"

    upstream_timeout_seconds: float = 10.0

    log_level: str = "INFO"

    wappos_domain_admins_group: str = "wappos_domain_admins"

    wappos_service_account_secret_path: str = "/etc/yunohost/.wappos_api_service_secret"

    wappos_domain_owners_path: str = "/etc/yunohost/wappos_domain_owners.json"

    wappos_domain_admin_primary_path: str = "/etc/yunohost/wappos_domain_admin_primary.json"


settings = Settings()
