# Auteur : Patrick Ritaine
from pathlib import Path
from unittest.mock import patch

import pytest

import app


@pytest.fixture(autouse=True)
def _reset_branding_cache():
    app._branding_cache["value"] = None
    app._branding_cache["fetched_at"] = 0.0
    yield


@pytest.fixture(autouse=True)
def _no_public_settings_by_default():
    with patch.object(app, "_public_settings_safe", return_value={}):
        yield


def test_wappos_fallback_text_appears_on_login_page_when_no_logo_configured(client):
    resp = client.get("/")
    body = resp.data.decode()
    assert 'class="brand-fallback-text"' in body
    assert ">WAPPOS<" in body


def test_wappos_brand_mark_always_present_in_footer_anonymous(client):
    resp = client.get("/")
    body = resp.data.decode()
    assert 'class="wappos-brand-mark">WAPPOS<' in body


def test_wappos_brand_mark_always_present_in_footer_authenticated(logged_in_client):
    me = {"mail": "patrick@byrtn.fr", "groups": ["all_users"], "apps": {}}
    with patch.object(app, "_wappos_api_me", return_value=me):
        resp = logged_in_client.get("/")
    body = resp.data.decode()
    assert 'class="wappos-brand-mark">WAPPOS<' in body


def test_favicon_link_present_in_head(client):
    resp = client.get("/")
    body = resp.data.decode()
    assert '<link rel="icon" type="image/png" href="/static/favicon.png">' in body


def test_favicon_file_exists_on_disk():
    favicon = Path(__file__).parent.parent / "static" / "favicon.png"
    assert favicon.exists()
    assert favicon.stat().st_size > 0
