# Auteur : Patrick Ritaine
import base64

import app


def test_same_app_family_matches_base_id():
    assert app._same_app_family("wappos_admin.main", "wappos_admin")


def test_same_app_family_matches_multi_instance_suffix():
    assert app._same_app_family("wappos_admin__2.main", "wappos_admin")


def test_same_app_family_rejects_other_app():
    assert not app._same_app_family("grav.main", "wappos_admin")


def test_is_wappos_infra_app_true_for_wappos_prefixed():
    assert app._is_wappos_infra_app("wappos_api.main")


def test_is_wappos_infra_app_true_for_multi_instance():
    assert app._is_wappos_infra_app("wappos_portal__2.main")


def test_is_wappos_infra_app_false_for_regular_app():
    assert not app._is_wappos_infra_app("grav.main")


def test_safe_next_path_accepts_relative_path():
    assert app._safe_next_path("/support") == "/support"


def test_safe_next_path_rejects_none():
    assert app._safe_next_path(None) is None


def test_safe_next_path_rejects_empty_string():
    assert app._safe_next_path("") is None


def test_safe_next_path_rejects_protocol_relative_url():
    assert app._safe_next_path("//evil.example.com") is None


def test_safe_next_path_rejects_absolute_url():
    assert app._safe_next_path("https://evil.example.com/") is None


def test_safe_next_path_rejects_backslash():
    assert app._safe_next_path("/support\\evil") is None


def test_safe_next_path_rejects_newline():
    assert app._safe_next_path("/support\nSet-Cookie: evil") is None


def _b64(url: str) -> str:
    return base64.b64encode(url.encode("utf-8")).decode("ascii")


def test_safe_r_redirect_accepts_known_domain(monkeypatch):
    monkeypatch.setattr(app, "_known_domain_names", lambda: {"byrtn.fr", "adguard.byrtn.fr"})
    assert app._safe_r_redirect(_b64("https://adguard.byrtn.fr/")) == "https://adguard.byrtn.fr/"


def test_safe_r_redirect_rejects_unknown_domain(monkeypatch):
    monkeypatch.setattr(app, "_known_domain_names", lambda: {"byrtn.fr"})
    assert app._safe_r_redirect(_b64("https://evil.example.com/")) is None


def test_safe_r_redirect_rejects_non_https(monkeypatch):
    monkeypatch.setattr(app, "_known_domain_names", lambda: {"byrtn.fr"})
    assert app._safe_r_redirect(_b64("http://byrtn.fr/")) is None


def test_safe_r_redirect_rejects_none():
    assert app._safe_r_redirect(None) is None


def test_safe_r_redirect_rejects_invalid_base64():
    assert app._safe_r_redirect("not-valid-base64!!!") is None


def test_header_info_admin_role():
    info = app._header_info({"mail": "adminynh@byrtn.fr", "groups": ["admins", "all_users"]})
    assert info == {"mail": "adminynh@byrtn.fr", "role": "Administrateur"}


def test_header_info_user_role():
    info = app._header_info({"mail": "patrick@byrtn.fr", "groups": ["all_users"]})
    assert info == {"mail": "patrick@byrtn.fr", "role": "Utilisateur"}


def test_list_tiles_excludes_own_family_and_infra_apps():
    apps = {
        "grav.main": {"label": "Grav", "url": "https://byrtn.fr/"},
        "wappos_admin.main": {"label": "Admin", "url": "https://byrtn.fr/wappos-admin/"},
        "wappos_api.main": {"label": "API", "url": "https://byrtn.fr/api/"},
    }
    tiles = app._list_tiles(apps, user=None)
    assert [t["id"] for t in tiles] == ["grav.main"]


def test_list_tiles_respects_saved_order(monkeypatch, tmp_path):
    monkeypatch.setattr(app, "TILE_ORDER_DIR", tmp_path)
    apps = {
        "grav.main": {"label": "Grav", "url": "https://byrtn.fr/grav/"},
        "sogo.main": {"label": "SOGo", "url": "https://byrtn.fr/sogo/"},
    }
    app._save_order("patrick", ["sogo.main", "grav.main"])
    tiles = app._list_tiles(apps, user="patrick")
    assert [t["id"] for t in tiles] == ["sogo.main", "grav.main"]


def test_list_tiles_unranked_app_goes_last(monkeypatch, tmp_path):
    monkeypatch.setattr(app, "TILE_ORDER_DIR", tmp_path)
    apps = {
        "grav.main": {"label": "Grav", "url": "https://byrtn.fr/grav/"},
        "sogo.main": {"label": "SOGo", "url": "https://byrtn.fr/sogo/"},
        "new_app.main": {"label": "New", "url": "https://byrtn.fr/new/"},
    }
    app._save_order("patrick", ["sogo.main", "grav.main"])
    tiles = app._list_tiles(apps, user="patrick")
    assert [t["id"] for t in tiles] == ["sogo.main", "grav.main", "new_app.main"]


def test_order_file_sanitizes_user_name(monkeypatch, tmp_path):
    monkeypatch.setattr(app, "TILE_ORDER_DIR", tmp_path)
    path = app._order_file("patrick@byrtn.fr")
    assert path.name == "patrick_byrtn.fr.json"


def test_load_order_missing_file_returns_empty_list(monkeypatch, tmp_path):
    monkeypatch.setattr(app, "TILE_ORDER_DIR", tmp_path)
    assert app._load_order("nobody") == []


def test_load_order_corrupt_file_returns_empty_list(monkeypatch, tmp_path):
    monkeypatch.setattr(app, "TILE_ORDER_DIR", tmp_path)
    app._order_file("patrick").write_text("not json")
    assert app._load_order("patrick") == []


def test_save_then_load_order_roundtrip(monkeypatch, tmp_path):
    monkeypatch.setattr(app, "TILE_ORDER_DIR", tmp_path)
    app._save_order("patrick", ["a.main", "b.main"])
    assert app._load_order("patrick") == ["a.main", "b.main"]
