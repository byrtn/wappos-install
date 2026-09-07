# Auteur : Patrick Ritaine
from unittest.mock import patch

import requests

import app


def test_failed_system_units_parses_unit_names():
    fake_result = type("R", (), {"stdout": "unit-a.service loaded active failed\nunit-b.timer loaded active failed\n"})()
    with patch.object(app.subprocess, "run", return_value=fake_result):
        units = app._failed_system_units()
    assert units == ["unit-a.service", "unit-b.timer"]


def test_failed_system_units_no_failures_returns_empty_list():
    fake_result = type("R", (), {"stdout": ""})()
    with patch.object(app.subprocess, "run", return_value=fake_result):
        units = app._failed_system_units()
    assert units == []


def test_failed_system_units_returns_none_on_error():
    with patch.object(app.subprocess, "run", side_effect=OSError("systemctl not found")):
        units = app._failed_system_units()
    assert units is None


def _patch_all_dashboard_calls(**overrides):
    defaults = {
        "_failed_system_units": [],
        "_wappos_api_storage_mounts": [],
        "_wappos_api_services": [],
        "_wappos_api_admin_diagnosis": [],
        "_wappos_api_list_backups": {"archives": {}},
        "_wappos_api_available_updates": {"apps": [], "system": {}},
    }
    defaults.update(overrides)
    patches = [patch.object(app, name, return_value=value) if not isinstance(value, BaseException)
               else patch.object(app, name, side_effect=value)
               for name, value in defaults.items()]
    return patches


def test_dashboard_summary_all_calls_succeed():
    patches = _patch_all_dashboard_calls(
        _wappos_api_storage_mounts=[{"mountpoint": "/"}],
        _wappos_api_services=[{"status": "running"}, {"status": "failed"}],
        _wappos_api_admin_diagnosis=[{"error_count": 2, "warning_count": 1}],
        _wappos_api_available_updates={"apps": ["grav"], "system": {"kernel": {}}},
    )
    for p in patches:
        p.start()
    try:
        summary = app._dashboard_summary("tok")
    finally:
        for p in patches:
            p.stop()
    assert summary["services_total"] == 2
    assert summary["services_down"] == 1
    assert summary["diag_errors"] == 2
    assert summary["diag_warnings"] == 1
    assert summary["app_updates"] == 1
    assert summary["system_update_categories"] == 1
    assert summary["failed_units"] == []


def test_dashboard_summary_partial_failure_leaves_other_fields_populated():
    patches = _patch_all_dashboard_calls(
        _wappos_api_storage_mounts=requests.exceptions.ConnectionError(),
        _wappos_api_services=[{"status": "running"}],
    )
    for p in patches:
        p.start()
    try:
        summary = app._dashboard_summary("tok")
    finally:
        for p in patches:
            p.stop()
    assert summary["mounts"] is None
    assert summary["services_total"] == 1
    assert summary["services_down"] == 0


def test_dashboard_summary_last_backup_uses_most_recent_archive():
    patches = _patch_all_dashboard_calls(
        _wappos_api_list_backups={
            "archives": {
                "daily-2026-08-01": {"created_at": "2026-08-01 02:00:00"},
                "daily-2026-08-10": {"created_at": "2026-08-10 02:00:00"},
            }
        },
    )
    for p in patches:
        p.start()
    try:
        summary = app._dashboard_summary("tok")
    finally:
        for p in patches:
            p.stop()
    assert summary["last_backup"] == "2026-08-10 02:00:00"


def test_home_route_requires_authentication(client):
    resp = client.get("/")
    assert resp.status_code == 401


def test_home_route_renders_dashboard_for_authenticated_user(logged_in_client):
    patches = _patch_all_dashboard_calls()
    for p in patches:
        p.start()
    try:
        resp = logged_in_client.get("/")
    finally:
        for p in patches:
            p.stop()
    assert resp.status_code == 200


def test_standalone_services_status_installed_and_running():
    systemctl_result = type("R", (), {"stdout": "loaded\nactive\nrunning\nMon 2026-08-24 08:00:00 CEST\n"})()
    date_result = type("R", (), {"stdout": "1756022400\n", "returncode": 0})()

    def fake_run(cmd, **kwargs):
        return date_result if cmd[0] == "date" else systemctl_result

    with patch.object(app.subprocess, "run", side_effect=fake_run):
        services = app._standalone_services_status()
    assert len(services) == len(app._STANDALONE_SERVICES)
    for s in services:
        assert s["installed"] is True
        assert s["status"] == "running"
        assert s["since"] == 1756022400.0


def test_standalone_services_status_not_installed():
    fake_result = type("R", (), {"stdout": "not-found\ninactive\ndead\n\n"})()
    with patch.object(app.subprocess, "run", return_value=fake_result):
        services = app._standalone_services_status()
    for s in services:
        assert s["installed"] is False


def test_standalone_services_status_survives_subprocess_error():
    with patch.object(app.subprocess, "run", side_effect=OSError("systemctl not found")):
        services = app._standalone_services_status()
    assert len(services) == len(app._STANDALONE_SERVICES)
    for s in services:
        assert s["installed"] is False
