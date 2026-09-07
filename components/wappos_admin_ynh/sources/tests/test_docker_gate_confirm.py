from unittest.mock import MagicMock, patch

import pytest

import docker_gate as dg


def test_resolve_target_url_path_mode():
    url = dg.resolve_target_url("path", "dev.byrtn.fr", "", "/grafana", "")
    assert url == "https://dev.byrtn.fr/grafana"


def test_resolve_target_url_path_mode_normalizes_missing_slash():
    url = dg.resolve_target_url("path", "dev.byrtn.fr", "", "grafana", "")
    assert url == "https://dev.byrtn.fr/grafana"


def test_resolve_target_url_path_mode_requires_domain():
    with pytest.raises(dg.DockerGateError):
        dg.resolve_target_url("path", "", "", "/grafana", "")


def test_resolve_target_url_path_mode_rejects_invalid_path():
    with pytest.raises(dg.DockerGateError):
        dg.resolve_target_url("path", "dev.byrtn.fr", "", "/gra fana", "")


def test_resolve_target_url_subdomain_mode():
    url = dg.resolve_target_url("subdomain", "", "byrtn.fr", "", "grafana")
    assert url == "https://grafana.byrtn.fr/"


def test_resolve_target_url_subdomain_mode_requires_subdomain():
    with pytest.raises(dg.DockerGateError):
        dg.resolve_target_url("subdomain", "", "byrtn.fr", "", "")


def test_resolve_target_url_subdomain_mode_requires_parent():
    with pytest.raises(dg.DockerGateError):
        dg.resolve_target_url("subdomain", "", "", "", "grafana")


def test_normalize_catalogue_entry_extracts_port_and_volume():
    entry = dg._normalize_catalogue_entry({
        "type": 1, "title": "Adguard", "description": "Blocks ads.",
        "image": "adguard/adguardhome:latest", "logo": "https://example/logo.png",
        "categories": ["Other"],
        "ports": ["53:53/tcp"],
        "volumes": [{"container": "/opt/adguardhome/work"}],
    })
    assert entry == {
        "title": "Adguard", "description": "Blocks ads.", "image": "adguard/adguardhome:latest",
        "logo": "https://example/logo.png", "categories": ["Other"],
        "container_port": "53", "data_path": "/opt/adguardhome/work", "env_vars": {},
    }


def test_normalize_catalogue_entry_rejects_stack_templates():
    assert dg._normalize_catalogue_entry({"type": 3, "title": "Stack", "image": "foo"}) is None


def test_normalize_catalogue_entry_rejects_missing_image():
    assert dg._normalize_catalogue_entry({"type": 1, "title": "No image"}) is None


def test_normalize_catalogue_entry_handles_missing_ports_and_volumes():
    entry = dg._normalize_catalogue_entry({"type": 1, "title": "Adminer", "image": "adminer:latest"})
    assert entry["container_port"] is None
    assert entry["data_path"] is None


def test_normalize_catalogue_entry_extracts_declared_env_vars():
    entry = dg._normalize_catalogue_entry({
        "type": 1, "title": "Something", "image": "something:latest",
        "env": [
            {"name": "NODE_ENV", "default": "development"},
            {"name": "url", "default": "http://localhost/"},
            {"name": "SECRET_NO_DEFAULT"},
        ],
    })
    assert entry["env_vars"] == {"NODE_ENV": "development", "url": "http://localhost/"}


def test_normalize_catalogue_entry_applies_ghost_known_good_override():
    entry = dg._normalize_catalogue_entry({
        "type": 1, "title": "Ghost (container)", "image": "ghost:latest",
        "env": [{"name": "NODE_ENV", "default": "development"}],
    })
    assert entry["env_vars"] == {
        "NODE_ENV": "development",
        "database__client": "sqlite3",
        "database__connection__filename": "/var/lib/ghost/content/data/ghost.db",
    }


def test_normalize_catalogue_entry_ghost_override_applies_regardless_of_tag():
    entry = dg._normalize_catalogue_entry({"type": 1, "title": "Ghost", "image": "ghost:5-alpine"})
    assert entry["env_vars"]["database__client"] == "sqlite3"


def test_base_image_name_strips_tag_and_registry():
    assert dg._base_image_name("ghost:latest") == "ghost"
    assert dg._base_image_name("lscr.io/linuxserver/heimdall:latest") == "heimdall"
    assert dg._base_image_name("adguard/adguardhome") == "adguardhome"


def test_fetch_app_catalogue_uses_fresh_cache(monkeypatch, tmp_path):
    cache_file = tmp_path / "cache.json"
    cache_file.write_text('{"apps": [{"title": "Cached"}], "fetched_at": 9999999999.0}')
    monkeypatch.setattr(dg, "_CATALOGUE_CACHE_FILE", cache_file)
    with patch("docker_gate.requests.get") as mock_get:
        result = dg.fetch_app_catalogue()
    mock_get.assert_not_called()
    assert result["source"] == "cache"
    assert result["apps"] == [{"title": "Cached"}]


def test_fetch_app_catalogue_falls_back_to_stale_cache_on_network_error(monkeypatch, tmp_path):
    cache_file = tmp_path / "cache.json"
    cache_file.write_text('{"apps": [{"title": "Old"}], "fetched_at": 1.0}')
    monkeypatch.setattr(dg, "_CATALOGUE_CACHE_FILE", cache_file)
    with patch("docker_gate.requests.get", side_effect=dg.requests.RequestException("boom")):
        result = dg.fetch_app_catalogue()
    assert result["source"] == "stale_cache"
    assert result["apps"] == [{"title": "Old"}]


def test_fetch_app_catalogue_returns_empty_when_no_cache_and_network_fails(monkeypatch, tmp_path):
    cache_file = tmp_path / "cache.json"
    monkeypatch.setattr(dg, "_CATALOGUE_CACHE_FILE", cache_file)
    with patch("docker_gate.requests.get", side_effect=dg.requests.RequestException("boom")):
        result = dg.fetch_app_catalogue()
    assert result["source"] == "unavailable"
    assert result["apps"] == []


def test_fetch_app_catalogue_writes_cache_on_success(monkeypatch, tmp_path):
    cache_file = tmp_path / "sub" / "cache.json"
    monkeypatch.setattr(dg, "_CATALOGUE_CACHE_FILE", cache_file)
    fake_response = MagicMock()
    fake_response.json.return_value = {"templates": [
        {"type": 1, "title": "Adminer", "image": "adminer:latest"},
        {"type": 3, "title": "Ignored stack", "image": "foo"},
    ]}
    with patch("docker_gate.requests.get", return_value=fake_response):
        result = dg.fetch_app_catalogue()
    assert result["source"] == "live"
    assert len(result["apps"]) == 1
    assert cache_file.is_file()
