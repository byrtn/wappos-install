# Auteur : Patrick Ritaine
from unittest.mock import MagicMock, patch

import pytest

import docker_gate as dg


@pytest.fixture
def sample_app(monkeypatch, tmp_path):
    compose_file = tmp_path / "docker-compose.yml"
    compose_file.write_text("services: {}\n")
    entry = {
        "slug": "myapp",
        "container_name": "docker-gate-myapp",
        "compose_project": "docker-gate-myapp",
        "compose_file": str(compose_file),
    }
    monkeypatch.setattr(dg, "_load_state", lambda: [entry])
    return entry


def test_container_action_rejects_unknown_action(sample_app):
    with pytest.raises(dg.DockerGateError):
        dg.container_action("myapp", "delete-everything")


def test_container_action_rejects_unknown_slug(monkeypatch):
    monkeypatch.setattr(dg, "_load_state", lambda: [])
    with pytest.raises(dg.DockerGateError):
        dg.container_action("nobody", "start")


def test_container_action_missing_compose_file_raises(monkeypatch):
    monkeypatch.setattr(dg, "_load_state", lambda: [
        {"slug": "myapp", "compose_project": "docker-gate-myapp", "compose_file": "/does/not/exist.yml"}
    ])
    with pytest.raises(dg.DockerGateError):
        dg.container_action("myapp", "start")


def test_container_action_calls_run_docker_compose(sample_app):
    with patch.object(dg, "_run_docker_compose") as mocked:
        dg.container_action("myapp", "restart")
    mocked.assert_called_once()
    args = mocked.call_args[0]
    assert args[0] == "docker-gate-myapp"
    assert args[2] == ["restart"]


def test_get_container_logs_unknown_slug(monkeypatch):
    monkeypatch.setattr(dg, "_load_state", lambda: [])
    with pytest.raises(dg.DockerGateError):
        dg.get_container_logs("nobody")


def test_get_container_logs_no_container_name(monkeypatch):
    monkeypatch.setattr(dg, "_load_state", lambda: [{"slug": "myapp", "container_name": None}])
    with pytest.raises(dg.DockerGateError):
        dg.get_container_logs("myapp")


def test_get_container_logs_returns_decoded_text(sample_app):
    fake_container = MagicMock()
    fake_container.logs.return_value = b"line1\nline2\n"
    fake_client = MagicMock()
    fake_client.containers.get.return_value = fake_container
    with patch.object(dg, "_get_docker_client", return_value=fake_client):
        logs = dg.get_container_logs("myapp", tail=50)
    assert logs == "line1\nline2\n"
    fake_container.logs.assert_called_once_with(tail=50, timestamps=True)


def test_get_container_logs_container_not_found(sample_app):
    import docker as docker_lib
    fake_client = MagicMock()
    fake_client.containers.get.side_effect = docker_lib.errors.NotFound("not found")
    with patch.object(dg, "_get_docker_client", return_value=fake_client):
        with pytest.raises(dg.DockerGateError):
            dg.get_container_logs("myapp")


def test_list_apps_reports_real_container_status(monkeypatch):
    monkeypatch.setattr(dg, "_load_state", lambda: [{"slug": "myapp", "container_name": "docker-gate-myapp"}])
    monkeypatch.setattr(dg, "_save_state", lambda apps: None)
    monkeypatch.setattr(dg, "docker_available", lambda: True)
    fake_container = MagicMock()
    fake_container.name = "docker-gate-myapp"
    fake_container.status = "running"
    fake_client = MagicMock()
    fake_client.containers.list.return_value = [fake_container]
    with patch.object(dg, "_get_docker_client", return_value=fake_client):
        apps = dg.list_apps(None)
    assert apps[0]["container_status"] == "running"
    assert apps[0]["container_missing"] is False


def test_list_apps_missing_container_has_no_status(monkeypatch):
    monkeypatch.setattr(dg, "_load_state", lambda: [{"slug": "myapp", "container_name": "docker-gate-myapp"}])
    monkeypatch.setattr(dg, "_save_state", lambda apps: None)
    monkeypatch.setattr(dg, "docker_available", lambda: True)
    fake_client = MagicMock()
    fake_client.containers.list.return_value = []
    with patch.object(dg, "_get_docker_client", return_value=fake_client):
        apps = dg.list_apps(None)
    assert apps[0]["container_status"] is None
    assert apps[0]["container_missing"] is True


def test_list_apps_docker_unavailable(monkeypatch):
    monkeypatch.setattr(dg, "_load_state", lambda: [{"slug": "myapp", "container_name": "docker-gate-myapp"}])
    monkeypatch.setattr(dg, "_save_state", lambda apps: None)
    monkeypatch.setattr(dg, "docker_available", lambda: False)
    apps = dg.list_apps(None)
    assert apps[0]["container_status"] is None
    assert apps[0]["container_missing"] is None
