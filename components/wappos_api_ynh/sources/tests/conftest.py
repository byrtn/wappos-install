# Auteur : Patrick Ritaine

from __future__ import annotations

import pytest

from wappos_api.config import settings
from wappos_api.connectors import admin

YUNOHOST_API_BASE = settings.yunohost_api_base_url
PORTALAPI_BASE = settings.portalapi_base_url


@pytest.fixture(autouse=True)
def _isolate_admin_ttl_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(admin, "_TTL_CACHE_DIR", tmp_path / "wappos_api_cache")


@pytest.fixture
def admin_login_url() -> str:
    return f"{YUNOHOST_API_BASE}/login"


@pytest.fixture
def admin_users_url() -> str:
    return f"{YUNOHOST_API_BASE}/users"


@pytest.fixture
def portalapi_base_url() -> str:
    return PORTALAPI_BASE


@pytest.fixture
def portalapi_login_url() -> str:
    return f"{PORTALAPI_BASE}/login"


@pytest.fixture
def portalapi_public_url() -> str:
    return f"{PORTALAPI_BASE}/public"
