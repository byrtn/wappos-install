# Auteur : Patrick Ritaine
import json
from datetime import datetime, timedelta
from unittest.mock import patch

import backup_scheduler as bs


def _completed(stdout="", stderr="", returncode=0):
    class _Result:
        pass
    r = _Result()
    r.stdout = stdout
    r.stderr = stderr
    r.returncode = returncode
    return r


def test_run_backup_parses_clean_json_output():
    payload = json.dumps({"name": "20260824-100000", "size": 42, "results": {"apps": {}, "system": {}}})
    with patch.object(bs.subprocess, "run", return_value=_completed(stdout=payload)):
        result = bs._run_backup({"scope": "full"})
    assert result["status"] == "COMPLETE"
    assert result["name"] == "20260824-100000"


def test_run_backup_falls_back_to_backup_list_when_create_output_unparseable():
    now = datetime.now()
    recent_archive = (now).strftime("%Y%m%d-%H%M%S")
    list_payload = json.dumps({"archives": ["20260101-000000", recent_archive]})

    def _fake_run(cmd, **kwargs):
        if cmd[:2] == ["yunohost", "backup"] and "list" in cmd:
            return _completed(stdout=list_payload)
        return _completed(stdout="WARNING It's hightly recommended to stop sogo before backup", returncode=0)

    with patch.object(bs.subprocess, "run", side_effect=_fake_run):
        result = bs._run_backup({"scope": "full"})

    assert result["status"] == "COMPLETE"
    assert result["name"] == recent_archive
    assert "detail" in result


def test_run_backup_reports_error_when_no_matching_archive_found():
    list_payload = json.dumps({"archives": ["20200101-000000"]})

    def _fake_run(cmd, **kwargs):
        if cmd[:2] == ["yunohost", "backup"] and "list" in cmd:
            return _completed(stdout=list_payload)
        return _completed(stdout="not json at all", returncode=1)

    with patch.object(bs.subprocess, "run", side_effect=_fake_run):
        result = bs._run_backup({"scope": "full"})

    assert result["status"] == "ERROR"
    assert "sortie JSON illisible" in result["detail"]


def test_find_archive_created_after_returns_none_when_list_unparseable():
    with patch.object(bs.subprocess, "run", return_value=_completed(stdout="garbage")):
        assert bs._find_archive_created_after(datetime.now()) is None


def test_find_archive_created_after_ignores_archives_older_than_cutoff():
    old = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d-%H%M%S")
    payload = json.dumps({"archives": [old]})
    with patch.object(bs.subprocess, "run", return_value=_completed(stdout=payload)):
        assert bs._find_archive_created_after(datetime.now()) is None
