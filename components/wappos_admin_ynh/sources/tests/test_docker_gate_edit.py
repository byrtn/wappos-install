from unittest.mock import patch

import pytest
import yaml

import docker_gate as dg


def _write_compose(path, services, volumes=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = {"services": services}
    if volumes:
        doc["volumes"] = volumes
    path.write_text(yaml.safe_dump(doc, sort_keys=False))


@pytest.fixture
def grafana_entry(tmp_path):
    compose_file = tmp_path / "grafana" / "docker-compose.yml"
    _write_compose(compose_file, {
        "app": {
            "image": "grafana/grafana:latest",
            "container_name": "docker-gate-grafana",
            "restart": "unless-stopped",
            "ports": ["127.0.0.1:9101:3000/tcp"],
        },
    })
    entry = {
        "slug": "grafana", "image": "grafana/grafana:latest", "container_name": "docker-gate-grafana",
        "container_port": 3000, "host_port": 9101, "domain": "dev.byrtn.fr", "path": "/grafana",
        "mode": "path", "visibility": "admins", "yunohost_app_id": "redirect__3",
        "volume_name": None, "data_path": None, "env_var_keys": [], "network_name": "docker-gate-grafana-net",
        "companions": [], "config_files": [], "compose_project": "docker-gate-grafana",
        "compose_file": str(compose_file),
    }
    return entry


def test_read_current_env_vars_empty_when_none_set(monkeypatch, grafana_entry):
    monkeypatch.setattr(dg, "_load_state", lambda: [grafana_entry])
    assert dg.read_current_env_vars("grafana") == {}


def test_read_current_env_vars_returns_real_values(monkeypatch, tmp_path):
    compose_file = tmp_path / "app" / "docker-compose.yml"
    _write_compose(compose_file, {
        "app": {"image": "nginx", "container_name": "docker-gate-myapp", "environment": {"FOO": "bar"}},
    })
    entry = {"slug": "myapp", "container_name": "docker-gate-myapp", "compose_file": str(compose_file)}
    monkeypatch.setattr(dg, "_load_state", lambda: [entry])
    assert dg.read_current_env_vars("myapp") == {"FOO": "bar"}


def test_update_docker_app_unknown_app(monkeypatch):
    monkeypatch.setattr(dg, "_load_state", lambda: [])
    with pytest.raises(dg.DockerGateError):
        dg.update_docker_app("ghost", image="nginx", container_port=80)


def test_update_docker_app_rejects_missing_image(monkeypatch, grafana_entry):
    monkeypatch.setattr(dg, "_load_state", lambda: [grafana_entry])
    with pytest.raises(dg.DockerGateError):
        dg.update_docker_app("grafana", image="", container_port=3000)


def test_update_docker_app_changes_image_and_env(monkeypatch, grafana_entry):
    apps = [grafana_entry]
    monkeypatch.setattr(dg, "_load_state", lambda: apps)
    saved = {}
    monkeypatch.setattr(dg, "_save_state", lambda a: saved.setdefault("apps", a))

    with patch.object(dg, "_run_docker_compose") as run_compose:
        entry = dg.update_docker_app(
            "grafana", image="grafana/grafana:11.0.0", container_port=3000,
            env_vars={"GF_LOG_LEVEL": "debug"},
        )

    assert entry["image"] == "grafana/grafana:11.0.0"
    assert entry["env_var_keys"] == ["GF_LOG_LEVEL"]
    doc = yaml.safe_load(open(grafana_entry["compose_file"]))
    assert doc["services"]["app"]["image"] == "grafana/grafana:11.0.0"
    assert doc["services"]["app"]["environment"] == {"GF_LOG_LEVEL": "debug"}
    assert run_compose.call_count == 2


def test_update_docker_app_adds_and_removes_data_volume(monkeypatch, grafana_entry):
    monkeypatch.setattr(dg, "_load_state", lambda: [grafana_entry])
    monkeypatch.setattr(dg, "_save_state", lambda a: None)

    with patch.object(dg, "_run_docker_compose"):
        entry = dg.update_docker_app("grafana", image="grafana/grafana:latest", container_port=3000, data_path="/var/lib/grafana")
    assert entry["data_path"] == "/var/lib/grafana"
    assert entry["volume_name"] == "docker-gate-grafana-data"
    doc = yaml.safe_load(open(grafana_entry["compose_file"]))
    assert doc["services"]["app"]["volumes"] == ["docker-gate-grafana-data:/var/lib/grafana"]
    assert "docker-gate-grafana-data" in doc["volumes"]

    with patch.object(dg, "_run_docker_compose"):
        entry = dg.update_docker_app("grafana", image="grafana/grafana:latest", container_port=3000, data_path="")
    assert entry["data_path"] is None
    assert entry["volume_name"] is None
    doc = yaml.safe_load(open(grafana_entry["compose_file"]))
    assert "volumes" not in doc["services"]["app"]
    assert "volumes" not in doc


def test_update_docker_app_preserves_companion_services(monkeypatch, tmp_path):
    compose_file = tmp_path / "myapp" / "docker-compose.yml"
    _write_compose(compose_file, {
        "app": {"image": "old/image", "container_name": "docker-gate-myapp", "ports": ["127.0.0.1:9100:80/tcp"],
                "depends_on": ["db"]},
        "db": {"image": "postgres:16", "container_name": "docker-gate-myapp-db",
               "environment": {"POSTGRES_PASSWORD": "secret"}, "volumes": ["docker-gate-myapp-db-data:/var/lib/postgresql/data"]},
    }, volumes={"docker-gate-myapp-db-data": {"name": "docker-gate-myapp-db-data"}})
    entry = {
        "slug": "myapp", "image": "old/image", "container_name": "docker-gate-myapp", "container_port": 80,
        "host_port": 9100, "compose_project": "docker-gate-myapp", "compose_file": str(compose_file),
    }
    monkeypatch.setattr(dg, "_load_state", lambda: [entry])
    monkeypatch.setattr(dg, "_save_state", lambda a: None)

    with patch.object(dg, "_run_docker_compose"):
        dg.update_docker_app("myapp", image="new/image", container_port=80)

    doc = yaml.safe_load(open(compose_file))
    assert doc["services"]["app"]["image"] == "new/image"
    assert doc["services"]["db"]["image"] == "postgres:16"
    assert doc["services"]["db"]["environment"] == {"POSTGRES_PASSWORD": "secret"}
    assert doc["volumes"]["docker-gate-myapp-db-data"] == {"name": "docker-gate-myapp-db-data"}


def test_update_docker_app_missing_compose_file(monkeypatch, grafana_entry):
    grafana_entry["compose_file"] = "/nonexistent/docker-compose.yml"
    monkeypatch.setattr(dg, "_load_state", lambda: [grafana_entry])
    with pytest.raises(dg.DockerGateError):
        dg.update_docker_app("grafana", image="grafana/grafana:latest", container_port=3000)


def test_update_docker_app_url_updates_domain_and_path(monkeypatch, grafana_entry):
    apps = [grafana_entry]
    saved = {}
    monkeypatch.setattr(dg, "_load_state", lambda: apps)
    monkeypatch.setattr(dg, "_save_state", lambda a: saved.setdefault("apps", a))

    result = dg.update_docker_app_url("grafana", "wappos.fr", "/monitoring")

    assert result["domain"] == "wappos.fr"
    assert result["path"] == "/monitoring"
    assert saved["apps"][0]["domain"] == "wappos.fr"
    assert saved["apps"][0]["path"] == "/monitoring"


def test_update_docker_app_url_unknown_app(monkeypatch):
    monkeypatch.setattr(dg, "_load_state", lambda: [])
    with pytest.raises(dg.DockerGateError):
        dg.update_docker_app_url("unknown", "wappos.fr", "/x")
