from __future__ import annotations
# Auteur : Patrick Ritaine

import subprocess

import pytest

from wappos_api.connectors import adguard
from wappos_api.errors import UpstreamProtocolError, UpstreamValidationError


class _FakeCompletedProcess:
    def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _mock_run(monkeypatch: pytest.MonkeyPatch, result: _FakeCompletedProcess):
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        return result

    monkeypatch.setattr(subprocess, "run", fake_run)
    return captured


def test_is_installed_true(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_run(monkeypatch, _FakeCompletedProcess(0, stdout="1\n"))
    assert adguard.is_installed() is True


def test_is_installed_false(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_run(monkeypatch, _FakeCompletedProcess(0, stdout="0\n"))
    assert adguard.is_installed() is False


def test_list_rewrites_parses_output(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_run(
        monkeypatch,
        _FakeCompletedProcess(0, stdout="byrtn.local\t192.168.1.203\tTrue\nwappos.local\t192.168.1.110\tTrue\n"),
    )
    rewrites = adguard.list_rewrites()
    assert rewrites == [
        {"domain": "byrtn.local", "answer": "192.168.1.203", "enabled": True},
        {"domain": "wappos.local", "answer": "192.168.1.110", "enabled": True},
    ]


def test_list_rewrites_failure_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_run(monkeypatch, _FakeCompletedProcess(1, stderr="boom"))
    with pytest.raises(UpstreamProtocolError):
        adguard.list_rewrites()


def test_add_rewrite_calls_script_with_args(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = _mock_run(monkeypatch, _FakeCompletedProcess(0))
    adguard.add_rewrite("byrtn.local", "192.168.1.203")
    assert captured["cmd"][-3:] == ["add", "byrtn.local", "192.168.1.203"]


def test_add_rewrite_failure_raises_validation_error(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_run(monkeypatch, _FakeCompletedProcess(1, stderr="Domaine invalide"))
    with pytest.raises(UpstreamValidationError):
        adguard.add_rewrite("not a domain", "192.168.1.203")


def test_remove_rewrite_calls_script_with_args(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = _mock_run(monkeypatch, _FakeCompletedProcess(0))
    adguard.remove_rewrite("byrtn.local")
    assert captured["cmd"][-2:] == ["remove", "byrtn.local"]


def test_run_timeout_raises_upstream_protocol_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd, 15)

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(UpstreamProtocolError):
        adguard.is_installed()
