from unittest.mock import patch

import app as app_module
import docker_gate as dg


def test_removing_docker_gate_app_from_apps_page_calls_docker_cleanup(logged_in_client, monkeypatch):
    entry = {"slug": "ghost-container", "yunohost_app_id": "redirect__4"}
    monkeypatch.setattr(dg, "_load_state", lambda: [entry])
    monkeypatch.setattr(dg, "_save_state", lambda apps: None)

    with patch.object(dg, "remove_docker_app", return_value=[]) as remove_docker_app, \
         patch.object(app_module, "_wappos_api_remove_app") as remove_app:
        resp = logged_in_client.post("/apps/redirect__4/remove", data={})

    assert resp.status_code == 302
    remove_docker_app.assert_called_once()
    called_slug = remove_docker_app.call_args.args[0]
    assert called_slug == "ghost-container"
    remove_app.assert_not_called()


def test_removing_docker_gate_app_purge_deletes_data(logged_in_client, monkeypatch):
    entry = {"slug": "ghost-container", "yunohost_app_id": "redirect__4"}
    monkeypatch.setattr(dg, "_load_state", lambda: [entry])
    monkeypatch.setattr(dg, "_save_state", lambda apps: None)

    with patch.object(dg, "remove_docker_app", return_value=[]) as remove_docker_app:
        logged_in_client.post("/apps/redirect__4/remove", data={"purge": "1"})

    assert remove_docker_app.call_args.kwargs["delete_data"] is True


def test_removing_non_docker_gate_app_uses_native_path(logged_in_client, monkeypatch):
    monkeypatch.setattr(dg, "_load_state", lambda: [])

    with patch.object(dg, "remove_docker_app") as remove_docker_app, \
         patch.object(app_module, "_wappos_api_remove_app") as remove_app:
        resp = logged_in_client.post("/apps/grav/remove", data={})

    assert resp.status_code == 302
    remove_docker_app.assert_not_called()
    remove_app.assert_called_once()
