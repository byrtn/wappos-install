# Auteur : Patrick Ritaine
from pathlib import Path

from test_dashboard import _patch_all_dashboard_calls


def test_wappos_fallback_text_present_in_header_markup(logged_in_client):
    patches = _patch_all_dashboard_calls()
    for p in patches:
        p.start()
    try:
        resp = logged_in_client.get("/")
    finally:
        for p in patches:
            p.stop()
    body = resp.data.decode()
    assert '<span id="header-fallback-text">WAPPOS</span>' in body


def test_wappos_fallback_text_present_on_login_page(client):
    resp = client.get("/")
    body = resp.data.decode()
    assert 'id="login-fallback-text"' in body
    assert ">WAPPOS<" in body


def test_wappos_brand_mark_present_in_login_footer(client):
    resp = client.get("/")
    body = resp.data.decode()
    assert 'class="wappos-brand-mark">WAPPOS ADMIN<' in body


def test_wappos_brand_mark_present_in_authenticated_footer(logged_in_client):
    patches = _patch_all_dashboard_calls()
    for p in patches:
        p.start()
    try:
        resp = logged_in_client.get("/")
    finally:
        for p in patches:
            p.stop()
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
