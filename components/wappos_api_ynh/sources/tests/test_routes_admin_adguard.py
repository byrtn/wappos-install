from __future__ import annotations
# Auteur : Patrick Ritaine

import subprocess

import pytest
import respx
from fastapi.testclient import TestClient
from httpx import Response

from wappos_api.main import app

client = TestClient(app)


class _FakeCompletedProcess:
    def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _mock_script(monkeypatch: pytest.MonkeyPatch, result: _FakeCompletedProcess):
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        return result

    monkeypatch.setattr(subprocess, "run", fake_run)
    return captured


@respx.mock
def test_status_route_reports_installed(admin_login_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    domains_url = admin_login_url.replace("/login", "/domains")
    respx.get(domains_url).mock(return_value=Response(200, json={"domains": ["byrtn.fr"], "main": "byrtn.fr"}))
    _mock_script(monkeypatch, _FakeCompletedProcess(0, stdout="1\n"))

    response = client.get("/admin/adguard/status", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.json() == {"installed": True}


@respx.mock
def test_add_rewrite_rejects_unknown_domain(admin_login_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    domains_url = admin_login_url.replace("/login", "/domains")
    respx.get(domains_url).mock(return_value=Response(200, json={"domains": ["byrtn.fr"], "main": "byrtn.fr"}))
    _mock_script(monkeypatch, _FakeCompletedProcess(0))

    response = client.post(
        "/admin/adguard/rewrites",
        json={"domain": "evil.example.com", "answer": "192.168.1.203"},
        headers={"X-Admin-Token": "abc123"},
    )

    assert response.status_code == 400


@respx.mock
def test_add_rewrite_accepts_registered_domain(admin_login_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    domains_url = admin_login_url.replace("/login", "/domains")
    respx.get(domains_url).mock(
        return_value=Response(200, json={"domains": ["byrtn.local"], "main": "byrtn.fr"})
    )
    captured = _mock_script(monkeypatch, _FakeCompletedProcess(0))

    response = client.post(
        "/admin/adguard/rewrites",
        json={"domain": "byrtn.local", "answer": "192.168.1.203"},
        headers={"X-Admin-Token": "abc123"},
    )

    assert response.status_code == 204
    assert captured["cmd"][-3:] == ["add", "byrtn.local", "192.168.1.203"]


@respx.mock
def test_remove_rewrite_route(admin_login_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    domains_url = admin_login_url.replace("/login", "/domains")
    respx.get(domains_url).mock(return_value=Response(200, json={"domains": ["byrtn.fr"], "main": "byrtn.fr"}))
    captured = _mock_script(monkeypatch, _FakeCompletedProcess(0))

    response = client.delete("/admin/adguard/rewrites/byrtn.local", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 204
    assert captured["cmd"][-2:] == ["remove", "byrtn.local"]


def _mock_script_by_action(monkeypatch: pytest.MonkeyPatch, responses: dict):
    calls = []

    def fake_run(cmd, **kwargs):
        action = cmd[4]
        calls.append(cmd)
        return responses[action]

    monkeypatch.setattr(subprocess, "run", fake_run)
    return calls


@respx.mock
def test_add_local_domain_rejects_non_local_name(admin_login_url: str) -> None:
    response = client.post(
        "/admin/local-domains", json={"domain": "not-local.fr"}, headers={"X-Admin-Token": "abc123"}
    )
    assert response.status_code == 400


@respx.mock
def test_add_local_domain_rejects_multi_label_lan(admin_login_url: str) -> None:
    response = client.post(
        "/admin/local-domains", json={"domain": "sub.byrtn.lan"}, headers={"X-Admin-Token": "abc123"}
    )
    assert response.status_code == 400


@respx.mock
def test_add_local_domain_creates_domain_and_rewrite(
    admin_login_url: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    add_url = admin_login_url.replace("/login", "/domains")
    respx.post(add_url).mock(return_value=Response(200))
    calls = _mock_script_by_action(
        monkeypatch,
        {
            "check": _FakeCompletedProcess(0, stdout="1\n"),
            "lan-ip": _FakeCompletedProcess(0, stdout="192.168.1.203\n"),
            "add": _FakeCompletedProcess(0),
        },
    )

    response = client.post(
        "/admin/local-domains", json={"domain": "wappos.lan"}, headers={"X-Admin-Token": "abc123"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body == {"domain": "wappos.lan", "domain_added": True, "adguard_rewrite_added": True}
    assert calls[-1][-3:] == ["add", "wappos.lan", "192.168.1.203"]


@respx.mock
def test_add_local_domain_without_adguard_skips_rewrite(
    admin_login_url: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    add_url = admin_login_url.replace("/login", "/domains")
    respx.post(add_url).mock(return_value=Response(200))
    _mock_script_by_action(monkeypatch, {"check": _FakeCompletedProcess(0, stdout="0\n")})

    response = client.post(
        "/admin/local-domains", json={"domain": "wappos.lan"}, headers={"X-Admin-Token": "abc123"}
    )

    assert response.status_code == 200
    assert response.json() == {"domain": "wappos.lan", "domain_added": True, "adguard_rewrite_added": None}


@respx.mock
def test_remove_local_domain_removes_rewrite_then_domain(
    admin_login_url: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    remove_url = admin_login_url.replace("/login", "/domains/wappos.lan")
    respx.delete(remove_url).mock(return_value=Response(200))
    calls = _mock_script_by_action(
        monkeypatch,
        {
            "check": _FakeCompletedProcess(0, stdout="1\n"),
            "remove": _FakeCompletedProcess(0),
        },
    )

    response = client.delete("/admin/local-domains/wappos.lan", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.json() == {"domain": "wappos.lan", "domain_added": False, "adguard_rewrite_added": True}
    assert calls[-1][-2:] == ["remove", "wappos.lan"]
