from unittest.mock import MagicMock, patch

import docker_gate as dg


def _app_ids_sequence(*sets):
    it = iter(sets)
    return lambda: next(it)


def test_fetch_catalogue_logo_bytes_rejects_non_https():
    assert dg.fetch_catalogue_logo_bytes("http://example.com/logo.png") is None


def test_fetch_catalogue_logo_bytes_rejects_empty():
    assert dg.fetch_catalogue_logo_bytes("") is None
    assert dg.fetch_catalogue_logo_bytes(None) is None


def test_fetch_catalogue_logo_bytes_accepts_real_png():
    fake_response = MagicMock(status_code=200, content=dg._PNG_MAGIC + b"restofthefile")
    with patch("docker_gate.requests.get", return_value=fake_response):
        result = dg.fetch_catalogue_logo_bytes("https://example.com/logo.png")
    assert result == dg._PNG_MAGIC + b"restofthefile"


def test_fetch_catalogue_logo_bytes_rejects_non_png_content():
    fake_response = MagicMock(status_code=200, content=b"<html>404</html>")
    with patch("docker_gate.requests.get", return_value=fake_response):
        assert dg.fetch_catalogue_logo_bytes("https://example.com/logo.png") is None


def test_fetch_catalogue_logo_bytes_rejects_404():
    fake_response = MagicMock(status_code=404, content=b"")
    with patch("docker_gate.requests.get", return_value=fake_response):
        assert dg.fetch_catalogue_logo_bytes("https://example.com/logo.png") is None


def test_fetch_catalogue_logo_bytes_rejects_oversized():
    fake_response = MagicMock(status_code=200, content=dg._PNG_MAGIC + b"x" * dg._LOGO_MAX_BYTES)
    with patch("docker_gate.requests.get", return_value=fake_response):
        assert dg.fetch_catalogue_logo_bytes("https://example.com/logo.png") is None


def test_fetch_catalogue_logo_bytes_survives_network_error():
    with patch("docker_gate.requests.get", side_effect=dg.requests.RequestException("boom")):
        assert dg.fetch_catalogue_logo_bytes("https://example.com/logo.png") is None


def test_create_docker_app_applies_real_logo(monkeypatch, tmp_path):
    monkeypatch.setattr(dg, "_load_state", lambda: [])
    monkeypatch.setattr(dg, "_save_state", lambda apps: None)
    monkeypatch.setattr(dg, "_compose_dir", lambda slug: tmp_path / slug)
    monkeypatch.setattr(dg, "_pick_free_port", lambda: 9100)
    set_logo = MagicMock()

    with patch.object(dg, "_run_docker_compose"):
        entry = dg.create_docker_app(
            slug="ghost", image="ghost:latest", container_port=2368, mode="path",
            domain="dev.byrtn.fr", domain_parent="", path="/ghost", new_subdomain="",
            visibility="admins", logo_bytes=b"real-ghost-logo-bytes",
            add_domain_fn=lambda d: None, run_diagnosis_fn=lambda c: True, install_cert_fn=lambda d: None,
            domain_detail_fn=lambda d: {}, install_app_fn=lambda *a: None,
            list_app_ids_fn=_app_ids_sequence(set(), {"redirect__9"}),
            set_permission_logo_fn=set_logo,
        )

    set_logo.assert_called_once_with("redirect__9.main", "logo.png", b"real-ghost-logo-bytes")
    assert entry["warnings"] == []


def test_create_docker_app_without_logo_does_not_call_set_permission(monkeypatch, tmp_path):
    monkeypatch.setattr(dg, "_load_state", lambda: [])
    monkeypatch.setattr(dg, "_save_state", lambda apps: None)
    monkeypatch.setattr(dg, "_compose_dir", lambda slug: tmp_path / slug)
    monkeypatch.setattr(dg, "_pick_free_port", lambda: 9100)
    set_logo = MagicMock()

    with patch.object(dg, "_run_docker_compose"):
        dg.create_docker_app(
            slug="myapp", image="nginx", container_port=80, mode="path",
            domain="dev.byrtn.fr", domain_parent="", path="/myapp", new_subdomain="",
            visibility="admins",
            add_domain_fn=lambda d: None, run_diagnosis_fn=lambda c: True, install_cert_fn=lambda d: None,
            domain_detail_fn=lambda d: {}, install_app_fn=lambda *a: None,
            list_app_ids_fn=_app_ids_sequence(set(), {"redirect__9"}),
            set_permission_logo_fn=set_logo,
        )
    set_logo.assert_not_called()


def test_create_docker_app_logo_failure_is_a_warning_not_a_crash(monkeypatch, tmp_path):
    monkeypatch.setattr(dg, "_load_state", lambda: [])
    monkeypatch.setattr(dg, "_save_state", lambda apps: None)
    monkeypatch.setattr(dg, "_compose_dir", lambda slug: tmp_path / slug)
    monkeypatch.setattr(dg, "_pick_free_port", lambda: 9100)

    def _boom(*a):
        raise RuntimeError("upstream rejected the file")

    with patch.object(dg, "_run_docker_compose"):
        entry = dg.create_docker_app(
            slug="ghost", image="ghost:latest", container_port=2368, mode="path",
            domain="dev.byrtn.fr", domain_parent="", path="/ghost", new_subdomain="",
            visibility="admins", logo_bytes=b"whatever",
            add_domain_fn=lambda d: None, run_diagnosis_fn=lambda c: True, install_cert_fn=lambda d: None,
            domain_detail_fn=lambda d: {}, install_app_fn=lambda *a: None,
            list_app_ids_fn=_app_ids_sequence(set(), {"redirect__9"}),
            set_permission_logo_fn=_boom,
        )
    assert entry["warnings"]
    assert "logo" in entry["warnings"][0].lower()
