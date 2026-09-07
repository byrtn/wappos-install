from __future__ import annotations
# Auteur : Patrick Ritaine

import subprocess

import pytest

from wappos_api.connectors import domains_public
from wappos_api.errors import UpstreamProtocolError


class _FakeCompletedProcess:
    def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _mock_run(monkeypatch: pytest.MonkeyPatch, result: _FakeCompletedProcess):
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kwargs: result)


def test_list_domain_names_parses_output(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_run(monkeypatch, _FakeCompletedProcess(0, stdout='{"domains": ["byrtn.fr", "wappos.lan"]}'))
    assert domains_public.list_domain_names() == ["byrtn.fr", "wappos.lan"]


def test_list_domain_names_command_failure_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_run(monkeypatch, _FakeCompletedProcess(1, stderr="boom"))
    with pytest.raises(UpstreamProtocolError):
        domains_public.list_domain_names()


def test_list_domain_names_invalid_json_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_run(monkeypatch, _FakeCompletedProcess(0, stdout="not json"))
    with pytest.raises(UpstreamProtocolError):
        domains_public.list_domain_names()
