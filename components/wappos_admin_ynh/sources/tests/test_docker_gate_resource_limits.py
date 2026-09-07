from unittest.mock import patch

import pytest

import docker_gate as dg


def test_validate_cpu_limit_accepts_decimal():
    assert dg._validate_cpu_limit("0.5") == "0.5"


def test_validate_cpu_limit_accepts_integer():
    assert dg._validate_cpu_limit("2") == "2"


def test_validate_cpu_limit_accepts_empty():
    assert dg._validate_cpu_limit("") is None
    assert dg._validate_cpu_limit(None) is None


def test_validate_cpu_limit_rejects_zero():
    with pytest.raises(dg.DockerGateError):
        dg._validate_cpu_limit("0")


def test_validate_cpu_limit_rejects_garbage():
    with pytest.raises(dg.DockerGateError):
        dg._validate_cpu_limit("beaucoup")


def test_validate_mem_limit_accepts_suffixed_value():
    assert dg._validate_mem_limit("512m") == "512m"
    assert dg._validate_mem_limit("1G") == "1G"


def test_validate_mem_limit_rejects_bare_number():
    with pytest.raises(dg.DockerGateError):
        dg._validate_mem_limit("2048")


def test_validate_mem_limit_rejects_kilobytes():
    with pytest.raises(dg.DockerGateError):
        dg._validate_mem_limit("512k")


def test_validate_mem_limit_accepts_empty():
    assert dg._validate_mem_limit("") is None
    assert dg._validate_mem_limit(None) is None


def test_validate_mem_limit_rejects_garbage():
    with pytest.raises(dg.DockerGateError):
        dg._validate_mem_limit("512 Mo")


def test_build_compose_document_no_limits_unchanged():
    doc = dg._build_compose_document("myapp", "app", "nginx", 80, 9100, None, "", [])
    assert "cpus" not in doc["services"]["app"]
    assert "mem_limit" not in doc["services"]["app"]


def test_build_compose_document_with_limits():
    doc = dg._build_compose_document("myapp", "app", "nginx", 80, 9100, None, "", [], cpu_limit="0.5", mem_limit="512m")
    assert doc["services"]["app"]["cpus"] == "0.5"
    assert doc["services"]["app"]["mem_limit"] == "512m"


def test_create_docker_app_persists_resource_limits(monkeypatch, tmp_path):
    monkeypatch.setattr(dg, "_load_state", lambda: [])
    monkeypatch.setattr(dg, "_save_state", lambda apps: None)
    monkeypatch.setattr(dg, "_compose_dir", lambda slug: tmp_path / slug)
    monkeypatch.setattr(dg, "_pick_free_port", lambda: 9100)

    with patch.object(dg, "_run_docker_compose"):
        entry = dg.create_docker_app(
            slug="myapp", image="nginx", container_port=80, mode="path",
            domain="dev.byrtn.fr", domain_parent="", path="/myapp", new_subdomain="",
            visibility="admins", cpu_limit="0.5", mem_limit="512m",
            add_domain_fn=lambda d: None, run_diagnosis_fn=lambda c: True, install_cert_fn=lambda d: None,
            domain_detail_fn=lambda d: {}, install_app_fn=lambda *a: None,
            list_app_ids_fn=lambda: set(),
        )

    assert entry["cpu_limit"] == "0.5"
    assert entry["mem_limit"] == "512m"


def test_create_docker_app_rejects_invalid_cpu_limit(monkeypatch, tmp_path):
    monkeypatch.setattr(dg, "_load_state", lambda: [])
    monkeypatch.setattr(dg, "_compose_dir", lambda slug: tmp_path / slug)
    monkeypatch.setattr(dg, "_pick_free_port", lambda: 9100)

    with pytest.raises(dg.DockerGateError):
        dg.create_docker_app(
            slug="myapp", image="nginx", container_port=80, mode="path",
            domain="dev.byrtn.fr", domain_parent="", path="/myapp", new_subdomain="",
            visibility="admins", cpu_limit="beaucoup",
            add_domain_fn=lambda d: None, run_diagnosis_fn=lambda c: True, install_cert_fn=lambda d: None,
            domain_detail_fn=lambda d: {}, install_app_fn=lambda *a: None,
            list_app_ids_fn=lambda: set(),
        )
