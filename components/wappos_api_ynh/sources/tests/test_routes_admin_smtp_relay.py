from __future__ import annotations
# Auteur : Patrick Ritaine

import subprocess

import pytest
from fastapi.testclient import TestClient

from wappos_api.connectors import admin as admin_connector
from wappos_api.main import app

client = TestClient(app)


class _FakeCompletedProcess:
    def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _domain_admin_token(monkeypatch: pytest.MonkeyPatch, owned_domains: list[str]) -> str:
    token = admin_connector._create_domain_admin_session("domain.admin")
    monkeypatch.setattr(
        "wappos_api.connectors.domain_owners.domains_owned_by", lambda username: owned_domains
    )
    monkeypatch.setattr(admin_connector, "_service_session_token", lambda: "service-session-token")
    return token


def test_get_smtp_relay_returns_none_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(cmd, **kw):
        return _FakeCompletedProcess(0, stdout="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    response = client.get("/admin/domains/dev.byrtn.fr/smtp-relay", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.json() is None


def test_get_smtp_relay_forbidden_outside_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.get("/admin/domains/dev.wappos.fr/smtp-relay", headers={"X-Admin-Token": token})

    assert response.status_code == 403


def test_set_smtp_relay_forbidden_outside_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.put(
        "/admin/domains/dev.wappos.fr/smtp-relay",
        json={"host": "smtp.example.com", "port": 587, "user": "u", "password": "p"},
        headers={"X-Admin-Token": token},
    )

    assert response.status_code == 403


def test_set_smtp_relay_allowed_inside_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    def fake_run(cmd, **kw):
        return _FakeCompletedProcess(0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    response = client.put(
        "/admin/domains/dev.byrtn.fr/smtp-relay",
        json={"host": "smtp.example.com", "port": 587, "user": "u", "password": "p"},
        headers={"X-Admin-Token": token},
    )

    assert response.status_code == 204


def test_set_smtp_relay_returns_400_on_script_validation_error(monkeypatch: pytest.MonkeyPatch) -> None:
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    def fake_run(cmd, **kw):
        return _FakeCompletedProcess(1, stderr="Port invalide")

    monkeypatch.setattr(subprocess, "run", fake_run)

    response = client.put(
        "/admin/domains/dev.byrtn.fr/smtp-relay",
        json={"host": "smtp.example.com", "port": 999999, "user": "u", "password": "p"},
        headers={"X-Admin-Token": token},
    )

    assert response.status_code == 400


def test_remove_smtp_relay_forbidden_outside_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.request(
        "DELETE", "/admin/domains/dev.wappos.fr/smtp-relay", headers={"X-Admin-Token": token}
    )

    assert response.status_code == 403


def test_remove_smtp_relay_allowed_inside_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    def fake_run(cmd, **kw):
        return _FakeCompletedProcess(0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    response = client.request(
        "DELETE", "/admin/domains/dev.byrtn.fr/smtp-relay", headers={"X-Admin-Token": token}
    )

    assert response.status_code == 204
