import threading
import time
from unittest.mock import patch

import docker_gate as dg


def _seed(monkeypatch, tmp_path, apps):
    data_file = tmp_path / "docker_apps.json"
    lock_file = tmp_path / "docker_port.lock"
    monkeypatch.setattr(dg, "DATA_FILE", data_file)
    monkeypatch.setattr(dg, "_STATE_LOCK_FILE", lock_file)
    dg._save_state(apps)
    return data_file


def _slow_run_docker_compose(*args, **kwargs):
    time.sleep(0.2)


def test_concurrent_updates_on_different_apps_do_not_lose_data(monkeypatch, tmp_path):
    apps = [
        {
            "slug": "app-a", "image": "nginx:latest", "container_name": "docker-gate-app-a",
            "compose_project": "docker-gate-app-a", "compose_file": str(tmp_path / "a.yml"),
            "host_port": 9101,
        },
        {
            "slug": "app-b", "image": "nginx:latest", "container_name": "docker-gate-app-b",
            "compose_project": "docker-gate-app-b", "compose_file": str(tmp_path / "b.yml"),
            "host_port": 9102,
        },
    ]
    (tmp_path / "a.yml").write_text("services:\n  app:\n    image: nginx:latest\n    container_name: docker-gate-app-a\n")
    (tmp_path / "b.yml").write_text("services:\n  app:\n    image: nginx:latest\n    container_name: docker-gate-app-b\n")
    _seed(monkeypatch, tmp_path, apps)

    errors = []

    def update(slug, new_image):
        try:
            with patch.object(dg, "_run_docker_compose", side_effect=_slow_run_docker_compose):
                dg.update_docker_app(slug, new_image, 80)
        except Exception as e:
            errors.append(e)

    t1 = threading.Thread(target=update, args=("app-a", "nginx:1.27"))
    t2 = threading.Thread(target=update, args=("app-b", "nginx:1.28"))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert not errors
    final = dg._load_state()
    by_slug = {a["slug"]: a for a in final}
    assert len(final) == 2
    assert by_slug["app-a"]["image"] == "nginx:1.27"
    assert by_slug["app-b"]["image"] == "nginx:1.28"


def test_concurrent_create_and_remove_do_not_corrupt_state(monkeypatch, tmp_path):
    existing = {
        "slug": "keep-me", "image": "nginx:latest", "container_name": "docker-gate-keep-me",
        "compose_project": "docker-gate-keep-me", "compose_file": str(tmp_path / "keep.yml"),
        "host_port": 9103, "yunohost_app_id": None, "compose_dir": str(tmp_path),
    }
    (tmp_path / "keep.yml").write_text("services:\n  app:\n    image: nginx:latest\n    container_name: docker-gate-keep-me\n")
    _seed(monkeypatch, tmp_path, [existing])

    to_remove = {
        "slug": "remove-me", "image": "nginx:latest", "container_name": "docker-gate-remove-me",
        "compose_project": "docker-gate-remove-me", "compose_file": None, "host_port": 9104,
        "yunohost_app_id": None,
    }
    apps = dg._load_state()
    apps.append(to_remove)
    dg._save_state(apps)

    errors = []

    def do_remove():
        try:
            dg.remove_docker_app("remove-me", remove_app_fn=lambda x: None)
        except Exception as e:
            errors.append(e)

    def do_update_url():
        try:
            with dg._state_lock():
                time.sleep(0.15)
                apps2, entry = dg._find_entry("keep-me")
                entry["domain"] = "example.org"
                dg._save_state(apps2)
        except Exception as e:
            errors.append(e)

    t1 = threading.Thread(target=do_update_url)
    t2 = threading.Thread(target=do_remove)
    t1.start()
    time.sleep(0.02)
    t2.start()
    t1.join()
    t2.join()

    assert not errors
    final = dg._load_state()
    slugs = {a["slug"] for a in final}
    assert slugs == {"keep-me"}
    assert next(a for a in final if a["slug"] == "keep-me")["domain"] == "example.org"


def test_list_apps_self_heal_does_not_block_when_lock_held(monkeypatch, tmp_path):
    apps = [
        {"slug": "a", "yunohost_app_id": "stale_app", "container_name": "docker-gate-a"},
    ]
    _seed(monkeypatch, tmp_path, apps)
    monkeypatch.setattr(dg, "docker_available", lambda: False)

    with dg._state_lock():
        result = dg.list_apps(real_yunohost_app_ids=set())

    assert len(result) == 1
    on_disk = dg._load_state()
    assert len(on_disk) == 1
