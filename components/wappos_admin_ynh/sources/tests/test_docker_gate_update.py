from unittest.mock import MagicMock, patch

import pytest

import docker_gate as dg


@pytest.fixture
def sample_app(monkeypatch, tmp_path):
    compose_file = tmp_path / "docker-compose.yml"
    compose_file.write_text(
        "services:\n"
        "  app:\n"
        "    image: grafana/grafana:11.2.0\n"
        "    container_name: docker-gate-myapp\n"
    )
    entry = {
        "slug": "myapp",
        "image": "grafana/grafana:11.2.0",
        "container_name": "docker-gate-myapp",
        "compose_project": "docker-gate-myapp",
        "compose_file": str(compose_file),
    }
    monkeypatch.setattr(dg, "_load_state", lambda: [entry])
    return entry


def test_docker_hub_repository_ref_official_image():
    assert dg._docker_hub_repository_ref("nginx:latest") == ("library", "nginx")


def test_docker_hub_repository_ref_namespaced_image():
    assert dg._docker_hub_repository_ref("grafana/grafana:11.2.0") == ("grafana", "grafana")


def test_docker_hub_repository_ref_private_registry_returns_none():
    assert dg._docker_hub_repository_ref("registry.example.com/team/app:1.0") is None
    assert dg._docker_hub_repository_ref("localhost:5000/app:1.0") is None


def test_list_available_image_tags_private_registry_raises():
    with pytest.raises(dg.DockerGateError):
        dg.list_available_image_tags("registry.example.com/team/app:1.0")


def test_list_available_image_tags_parses_response():
    fake_response = MagicMock()
    fake_response.json.return_value = {
        "results": [
            {"name": "11.3.0", "last_updated": "2026-08-20T10:00:00Z", "digest": "sha256:aaa"},
            {"name": "latest", "last_updated": "2026-08-20T10:00:00Z", "digest": "sha256:aaa"},
        ]
    }
    fake_response.raise_for_status.return_value = None
    with patch.object(dg.requests, "get", return_value=fake_response) as mocked:
        tags = dg.list_available_image_tags("grafana/grafana:11.2.0")

    assert [t["name"] for t in tags] == ["11.3.0", "latest"]
    called_url = mocked.call_args[0][0]
    assert called_url == "https://hub.docker.com/v2/repositories/grafana/grafana/tags"


def test_list_available_image_tags_network_error_raises():
    import requests as requests_lib
    with patch.object(dg.requests, "get", side_effect=requests_lib.exceptions.ConnectionError("down")):
        with pytest.raises(dg.DockerGateError):
            dg.list_available_image_tags("grafana/grafana:11.2.0")


def test_check_docker_app_update_unknown_slug(monkeypatch):
    monkeypatch.setattr(dg, "_load_state", lambda: [])
    with pytest.raises(dg.DockerGateError):
        dg.check_docker_app_update("nobody")


def test_check_docker_app_update_detects_available(sample_app):
    fake_container = MagicMock()
    fake_container.image.id = "sha256:old"
    fake_client = MagicMock()
    fake_client.containers.get.return_value = fake_container
    fake_client.images.get_registry_data.return_value = MagicMock(id="sha256:new")
    with patch.object(dg, "_get_docker_client", return_value=fake_client):
        result = dg.check_docker_app_update("myapp")

    assert result["checked"] is True
    assert result["update_available"] is True
    assert result["current_digest"] == "sha256:old"
    assert result["latest_digest"] == "sha256:new"


def test_check_docker_app_update_up_to_date(sample_app):
    fake_container = MagicMock()
    fake_container.image.id = "sha256:same"
    fake_client = MagicMock()
    fake_client.containers.get.return_value = fake_container
    fake_client.images.get_registry_data.return_value = MagicMock(id="sha256:same")
    with patch.object(dg, "_get_docker_client", return_value=fake_client):
        result = dg.check_docker_app_update("myapp")

    assert result["update_available"] is False


def test_check_docker_app_update_container_not_found(sample_app):
    import docker as docker_lib
    fake_client = MagicMock()
    fake_client.containers.get.side_effect = docker_lib.errors.NotFound("nope")
    with patch.object(dg, "_get_docker_client", return_value=fake_client):
        result = dg.check_docker_app_update("myapp")

    assert result["checked"] is False


def test_check_docker_app_update_registry_unreachable_does_not_raise(sample_app):
    import docker as docker_lib
    fake_container = MagicMock()
    fake_container.image.id = "sha256:old"
    fake_client = MagicMock()
    fake_client.containers.get.return_value = fake_container
    fake_client.images.get_registry_data.side_effect = docker_lib.errors.APIError("unreachable")
    with patch.object(dg, "_get_docker_client", return_value=fake_client):
        result = dg.check_docker_app_update("myapp")

    assert result["checked"] is False
    assert "error" in result


def test_apply_docker_app_update_pulls_and_restarts_same_tag(sample_app):
    with patch.object(dg, "_run_docker_compose") as mocked:
        entry = dg.apply_docker_app_update("myapp")

    assert entry["image"] == "grafana/grafana:11.2.0"
    calls = [c.args[2] for c in mocked.call_args_list]
    assert ["pull"] in calls
    assert ["up", "-d", "--wait", "--wait-timeout", "120"] in calls


def test_apply_docker_app_update_switches_target_tag(sample_app):
    with patch.object(dg, "_run_docker_compose"):
        entry = dg.apply_docker_app_update("myapp", target_tag="11.3.0")

    assert entry["image"] == "grafana/grafana:11.3.0"


def test_apply_docker_app_update_missing_compose_raises(monkeypatch):
    monkeypatch.setattr(dg, "_load_state", lambda: [
        {"slug": "myapp", "image": "nginx:latest", "compose_file": "/does/not/exist.yml"}
    ])
    with pytest.raises(dg.DockerGateError):
        dg.apply_docker_app_update("myapp")
