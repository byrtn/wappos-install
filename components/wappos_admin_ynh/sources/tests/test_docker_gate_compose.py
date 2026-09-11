# Auteur : Patrick Ritaine
from unittest.mock import patch

import pytest

import docker_gate as dg


def test_write_bind_mount_file_writes_content(monkeypatch, tmp_path):
    monkeypatch.setattr(dg, "_compose_dir", lambda slug: tmp_path / slug)
    dg._write_bind_mount_file("myapp", "prometheus.yml", "global:\n  scrape_interval: 15s\n")
    written = (tmp_path / "myapp" / "config" / "prometheus.yml").read_text()
    assert written == "global:\n  scrape_interval: 15s\n"


def test_write_bind_mount_file_rejects_path_traversal(monkeypatch, tmp_path):
    monkeypatch.setattr(dg, "_compose_dir", lambda slug: tmp_path / slug)
    with pytest.raises(dg.DockerGateError):
        dg._write_bind_mount_file("myapp", "../../etc/passwd", "evil")


def test_write_bind_mount_file_rejects_subdirectory(monkeypatch, tmp_path):
    monkeypatch.setattr(dg, "_compose_dir", lambda slug: tmp_path / slug)
    with pytest.raises(dg.DockerGateError):
        dg._write_bind_mount_file("myapp", "sub/dir/file.yml", "content")


def test_write_bind_mount_file_rejects_empty_name(monkeypatch, tmp_path):
    monkeypatch.setattr(dg, "_compose_dir", lambda slug: tmp_path / slug)
    with pytest.raises(dg.DockerGateError):
        dg._write_bind_mount_file("myapp", "", "content")


def test_build_compose_document_no_volumes_unchanged():
    doc = dg._build_compose_document("myapp", "app", "nginx", 80, 9100, None, "", [])
    assert "volumes" not in doc["services"]["app"]
    assert "volumes" not in doc


def test_build_compose_document_data_path_only():
    doc = dg._build_compose_document("myapp", "app", "nginx", 80, 9100, None, "/data", [])
    assert doc["services"]["app"]["volumes"] == ["docker-gate-myapp-data:/data"]
    assert "docker-gate-myapp-data" in doc["volumes"]


def test_build_compose_document_config_file_only():
    doc = dg._build_compose_document(
        "myapp", "app", "prom/prometheus", 9090, 9100, None, "",
        [], config_files=[{"container_path": "/etc/prometheus/prometheus.yml", "host_relative_path": "prometheus.yml"}],
    )
    assert doc["services"]["app"]["volumes"] == ["./config/prometheus.yml:/etc/prometheus/prometheus.yml:ro"]
    assert "volumes" not in doc


def test_build_compose_document_data_path_and_config_file_combined():
    doc = dg._build_compose_document(
        "myapp", "app", "prom/prometheus", 9090, 9100, None, "/prometheus",
        [], config_files=[{"container_path": "/etc/prometheus/prometheus.yml", "host_relative_path": "prometheus.yml"}],
    )
    volumes = doc["services"]["app"]["volumes"]
    assert "docker-gate-myapp-data:/prometheus" in volumes
    assert "./config/prometheus.yml:/etc/prometheus/prometheus.yml:ro" in volumes
    assert len(volumes) == 2


def test_create_docker_app_writes_config_files_and_builds_compose(monkeypatch, tmp_path):
    monkeypatch.setattr(dg, "_load_state", lambda: [])
    monkeypatch.setattr(dg, "_save_state", lambda apps: None)
    monkeypatch.setattr(dg, "_compose_dir", lambda slug: tmp_path / slug)
    monkeypatch.setattr(dg, "_pick_free_port", lambda **kwargs: 9100)

    with patch.object(dg, "_run_docker_compose") as run_compose:
        entry = dg.create_docker_app(
            slug="prometheus", image="prom/prometheus", container_port=9090, mode="path",
            domain="dev.byrtn.fr", domain_parent="", path="/prometheus", new_subdomain="",
            visibility="admins", data_path="/prometheus",
            config_files=[{"container_path": "/etc/prometheus/prometheus.yml", "filename": "prometheus.yml",
                            "content": "global:\n  scrape_interval: 15s\n"}],
            add_domain_fn=lambda d: None, run_diagnosis_fn=lambda c: True, install_cert_fn=lambda d: None,
            domain_detail_fn=lambda d: {}, install_app_fn=lambda *a: None,
            list_app_ids_fn=lambda: set(),
        )

    assert (tmp_path / "prometheus" / "config" / "prometheus.yml").read_text() == "global:\n  scrape_interval: 15s\n"
    assert entry["config_files"] == [{"container_path": "/etc/prometheus/prometheus.yml", "host_relative_path": "prometheus.yml"}]
    compose_doc_call = [c for c in run_compose.call_args_list if "config" in c[0][2]]
    assert compose_doc_call
