from __future__ import annotations
# Auteur : Patrick Ritaine

import subprocess

import pytest

from wappos_api.connectors import smtp_relay
from wappos_api.errors import UpstreamProtocolError, UpstreamValidationError


class _FakeCompletedProcess:
    def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_get_relay_returns_none_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: _FakeCompletedProcess(0, stdout=""))

    assert smtp_relay.get_relay("dev.byrtn.fr") is None


def test_get_relay_parses_json_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        subprocess, "run",
        lambda cmd, **kw: _FakeCompletedProcess(0, stdout='{"host": "smtp.example.com", "port": 587, "user": "u", "has_password": true}'),
    )

    result = smtp_relay.get_relay("dev.byrtn.fr")

    assert result == {"host": "smtp.example.com", "port": 587, "user": "u", "has_password": True}


def test_get_relay_raises_on_script_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: _FakeCompletedProcess(1, stderr="boom"))

    with pytest.raises(UpstreamProtocolError):
        smtp_relay.get_relay("dev.byrtn.fr")


def test_set_relay_calls_script_with_args(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    def fake_run(cmd, **kw):
        captured["cmd"] = cmd
        return _FakeCompletedProcess(0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    smtp_relay.set_relay("dev.byrtn.fr", "smtp.example.com", 587, "user", "pass")

    assert captured["cmd"][-6:] == ["set", "dev.byrtn.fr", "smtp.example.com", "587", "user", "pass"]


def test_set_relay_raises_validation_error_on_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: _FakeCompletedProcess(1, stderr="Domaine inconnu"))

    with pytest.raises(UpstreamValidationError):
        smtp_relay.set_relay("dev.byrtn.fr", "smtp.example.com", 587, "user", "pass")


def test_remove_relay_calls_script(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    def fake_run(cmd, **kw):
        captured["cmd"] = cmd
        return _FakeCompletedProcess(0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    smtp_relay.remove_relay("dev.byrtn.fr")

    assert captured["cmd"][-2:] == ["remove", "dev.byrtn.fr"]
