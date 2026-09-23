from __future__ import annotations
# Auteur : Patrick Ritaine

import subprocess

import pytest

from wappos_api.connectors import db_access
from wappos_api.errors import UpstreamProtocolError


class _FakeCompletedProcess:
    def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_list_all_parses_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        subprocess, "run", lambda cmd, **kw: _FakeCompletedProcess(0, stdout='{"nextcloud": {"db_name": "nextcloud", "db_user": "nextcloud"}}')
    )

    assert db_access.list_all() == {"nextcloud": {"db_name": "nextcloud", "db_user": "nextcloud"}}


def test_list_all_raises_on_script_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: _FakeCompletedProcess(1, stderr="boom"))

    with pytest.raises(UpstreamProtocolError):
        db_access.list_all()


def test_get_credentials_returns_none_when_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: _FakeCompletedProcess(0, stdout="null"))

    assert db_access.get_credentials("some_static_app") is None


def test_get_credentials_returns_parsed_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda cmd, **kw: _FakeCompletedProcess(0, stdout='{"db_name": "roundcube", "db_user": "roundcube", "db_pwd": "secret"}'),
    )

    assert db_access.get_credentials("roundcube") == {
        "db_name": "roundcube",
        "db_user": "roundcube",
        "db_pwd": "secret",
    }
