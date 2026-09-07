from unittest.mock import patch

import docker_gate as dg


def test_remove_stale_app_logo_calls_sudo_rm_for_numbered_redirect():
    with patch.object(dg.subprocess, "run") as run:
        dg._remove_stale_app_logo("redirect__4")
    run.assert_called_once_with(
        ["sudo", "-n", "rm", "-f", "/usr/share/yunohost/applogos/redirect__4.png"],
        capture_output=True, timeout=10,
    )


def test_remove_stale_app_logo_ignores_bare_redirect():
    with patch.object(dg.subprocess, "run") as run:
        dg._remove_stale_app_logo("redirect")
    run.assert_not_called()


def test_remove_stale_app_logo_ignores_unrelated_app_id():
    with patch.object(dg.subprocess, "run") as run:
        dg._remove_stale_app_logo("grav")
    run.assert_not_called()


def test_remove_stale_app_logo_survives_subprocess_error():
    with patch.object(dg.subprocess, "run", side_effect=OSError("no sudo")):
        dg._remove_stale_app_logo("redirect__4")


def test_remove_docker_app_cleans_up_logo(monkeypatch, tmp_path):
    entry = {
        "slug": "myapp", "yunohost_app_id": "redirect__4", "compose_project": None,
        "compose_file": None,
    }
    monkeypatch.setattr(dg, "_load_state", lambda: [entry])
    monkeypatch.setattr(dg, "_save_state", lambda apps: None)

    with patch.object(dg, "_remove_stale_app_logo") as cleanup:
        dg.remove_docker_app("myapp", remove_app_fn=lambda app_id: None)
    cleanup.assert_called_once_with("redirect__4")


def test_remove_docker_app_purge_removes_volume_and_image(monkeypatch, tmp_path):
    compose_file = tmp_path / "myapp" / "docker-compose.yml"
    compose_file.parent.mkdir(parents=True)
    compose_file.write_text("services: {}\n")
    entry = {
        "slug": "myapp", "yunohost_app_id": None, "compose_project": "docker-gate-myapp",
        "compose_file": str(compose_file),
    }
    monkeypatch.setattr(dg, "_load_state", lambda: [entry])
    monkeypatch.setattr(dg, "_save_state", lambda apps: None)

    with patch.object(dg, "_run_docker_compose") as run_compose:
        dg.remove_docker_app("myapp", delete_data=True, remove_app_fn=lambda app_id: None)
    args = run_compose.call_args.args[2]
    assert args == ["down", "-v", "--rmi", "all"]


def test_remove_docker_app_without_purge_keeps_volume_and_image(monkeypatch, tmp_path):
    compose_file = tmp_path / "myapp" / "docker-compose.yml"
    compose_file.parent.mkdir(parents=True)
    compose_file.write_text("services: {}\n")
    entry = {
        "slug": "myapp", "yunohost_app_id": None, "compose_project": "docker-gate-myapp",
        "compose_file": str(compose_file),
    }
    monkeypatch.setattr(dg, "_load_state", lambda: [entry])
    monkeypatch.setattr(dg, "_save_state", lambda apps: None)

    with patch.object(dg, "_run_docker_compose") as run_compose:
        dg.remove_docker_app("myapp", delete_data=False, remove_app_fn=lambda app_id: None)
    args = run_compose.call_args.args[2]
    assert args == ["down"]
