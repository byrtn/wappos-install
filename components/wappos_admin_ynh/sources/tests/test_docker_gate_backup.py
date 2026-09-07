from unittest.mock import MagicMock, patch

import pytest

import docker_gate as dg


@pytest.fixture
def sample_apps(monkeypatch):
    apps = [
        {
            "slug": "myapp",
            "volume_name": "docker-gate-myapp-data",
            "compose_project": "docker-gate-myapp",
            "compose_file": "/does/not/exist.yml",
            "companions": [],
        }
    ]
    monkeypatch.setattr(dg, "_load_state", lambda: apps)
    return apps


def test_backup_docker_volumes_runs_helper_container(sample_apps, tmp_path):
    fake_client = MagicMock()
    fake_client.volumes.get.return_value = MagicMock()

    def fake_run(*args, **kwargs):
        (tmp_path / "docker-gate-myapp-data.tar.gz").write_text("fake archive")

    fake_client.containers.run.side_effect = fake_run
    with patch.object(dg, "_get_docker_client", return_value=fake_client):
        results = dg.backup_docker_volumes(tmp_path)

    assert len(results) == 1
    assert results[0]["volume"] == "docker-gate-myapp-data"
    assert results[0]["status"] == "ok"
    fake_client.containers.run.assert_called_once()
    call_kwargs = fake_client.containers.run.call_args.kwargs
    assert "docker-gate-myapp-data" in call_kwargs["volumes"]


def test_backup_docker_volumes_missing_volume(sample_apps, tmp_path):
    import docker as docker_lib
    fake_client = MagicMock()
    fake_client.volumes.get.side_effect = docker_lib.errors.NotFound("nope")
    with patch.object(dg, "_get_docker_client", return_value=fake_client):
        results = dg.backup_docker_volumes(tmp_path)

    assert results[0]["status"] == "missing"
    fake_client.containers.run.assert_not_called()


def test_backup_docker_volumes_no_apps(monkeypatch, tmp_path):
    monkeypatch.setattr(dg, "_load_state", lambda: [])
    fake_client = MagicMock()
    with patch.object(dg, "_get_docker_client", return_value=fake_client):
        results = dg.backup_docker_volumes(tmp_path)
    assert results == []


def test_restore_docker_volumes_recreates_missing_volume(sample_apps, tmp_path):
    import docker as docker_lib
    archive = tmp_path / "docker-gate-myapp-data.tar.gz"
    archive.write_text("fake archive")

    fake_client = MagicMock()
    fake_client.volumes.get.side_effect = docker_lib.errors.NotFound("nope")
    with patch.object(dg, "_get_docker_client", return_value=fake_client):
        results = dg.restore_docker_volumes(tmp_path)

    assert results[0]["status"] == "ok"
    fake_client.volumes.create.assert_called_once_with(name="docker-gate-myapp-data")
    fake_client.containers.run.assert_called_once()


def test_restore_docker_volumes_skips_unknown_archive(sample_apps, tmp_path):
    (tmp_path / "unknown-volume.tar.gz").write_text("fake archive")
    fake_client = MagicMock()
    with patch.object(dg, "_get_docker_client", return_value=fake_client):
        results = dg.restore_docker_volumes(tmp_path)

    assert results[0]["status"] == "skipped_unknown"
    fake_client.containers.run.assert_not_called()


def test_restore_docker_volumes_missing_dir(sample_apps, tmp_path):
    fake_client = MagicMock()
    with patch.object(dg, "_get_docker_client", return_value=fake_client):
        results = dg.restore_docker_volumes(tmp_path / "does-not-exist")
    assert results == []


def test_restart_all_docker_apps_calls_compose_up(sample_apps, monkeypatch, tmp_path):
    compose_file = tmp_path / "docker-compose.yml"
    compose_file.write_text("services: {}\n")
    sample_apps[0]["compose_file"] = str(compose_file)

    with patch.object(dg, "_run_docker_compose") as mocked:
        results = dg.restart_all_docker_apps()

    assert results[0]["status"] == "started"
    mocked.assert_called_once()
    assert mocked.call_args[0][2] == ["up", "-d", "--wait", "--wait-timeout", "120"]


def test_restart_all_docker_apps_skips_missing_compose(sample_apps):
    results = dg.restart_all_docker_apps()
    assert results[0]["status"] == "skipped_no_compose"


def test_restart_all_docker_apps_one_failure_does_not_block_others(monkeypatch, tmp_path):
    ok_compose = tmp_path / "ok.yml"
    ok_compose.write_text("services: {}\n")
    apps = [
        {"slug": "broken", "compose_project": "docker-gate-broken", "compose_file": "/does/not/exist.yml"},
        {"slug": "ok", "compose_project": "docker-gate-ok", "compose_file": str(ok_compose)},
    ]
    monkeypatch.setattr(dg, "_load_state", lambda: apps)

    with patch.object(dg, "_run_docker_compose") as mocked:
        results = dg.restart_all_docker_apps()

    assert results[0]["status"] == "skipped_no_compose"
    assert results[1]["status"] == "started"
    mocked.assert_called_once()
