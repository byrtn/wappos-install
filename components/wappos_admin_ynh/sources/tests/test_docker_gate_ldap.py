from unittest.mock import MagicMock, patch

import docker_gate as dg


def test_ldap_env_vars_values():
    values = dg.ldap_env_vars()
    assert values["LDAP_HOST"] == "host.docker.internal"
    assert values["LDAP_PORT"] == "1389"
    assert values["LDAP_BASE_DN"] == "ou=users,dc=yunohost,dc=org"


def test_build_compose_document_without_ldap_unchanged():
    doc = dg._build_compose_document(
        slug="myapp", main_key="app", image="nginx:latest", container_port=80,
        host_port=9101, env_vars=None, data_path=None, companions=[],
    )
    main_service = doc["services"]["app"]
    assert "extra_hosts" not in main_service
    assert "environment" not in main_service


def test_build_compose_document_with_ldap_adds_env_and_extra_hosts():
    doc = dg._build_compose_document(
        slug="myapp", main_key="app", image="grafana/grafana:latest", container_port=3000,
        host_port=9101, env_vars={"GF_SERVER_ROOT_URL": "https://example.org/"}, data_path=None,
        companions=[], ldap_enabled=True,
    )
    main_service = doc["services"]["app"]
    assert main_service["extra_hosts"] == ["host.docker.internal:host-gateway"]
    assert main_service["environment"]["LDAP_HOST"] == "host.docker.internal"
    assert main_service["environment"]["LDAP_BASE_DN"] == "ou=users,dc=yunohost,dc=org"
    assert main_service["environment"]["GF_SERVER_ROOT_URL"] == "https://example.org/"


def test_apply_ldap_wiring_removes_extra_hosts_when_disabled():
    service = {"extra_hosts": ["host.docker.internal:host-gateway"]}
    dg._apply_ldap_wiring(service, False)
    assert "extra_hosts" not in service


def test_apply_ldap_wiring_does_not_duplicate_entry():
    service = {"extra_hosts": ["other.host:1.2.3.4"]}
    dg._apply_ldap_wiring(service, True)
    dg._apply_ldap_wiring(service, True)
    assert service["extra_hosts"].count("host.docker.internal:host-gateway") == 1
    assert "other.host:1.2.3.4" in service["extra_hosts"]


def test_update_docker_app_preserves_ldap_enabled_when_not_specified(monkeypatch, tmp_path):
    compose_file = tmp_path / "docker-compose.yml"
    compose_file.write_text(
        "services:\n  app:\n    image: nginx:latest\n    container_name: docker-gate-myapp\n"
    )
    entry = {
        "slug": "myapp", "image": "nginx:latest", "container_name": "docker-gate-myapp",
        "compose_project": "docker-gate-myapp", "compose_file": str(compose_file),
        "host_port": 9101, "ldap_enabled": True,
    }
    monkeypatch.setattr(dg, "_load_state", lambda: [entry])
    with patch.object(dg, "_run_docker_compose"), patch.object(dg, "ensure_ldap_relay") as mocked_relay:
        updated = dg.update_docker_app("myapp", image="nginx:latest", container_port=80)
    assert updated["ldap_enabled"] is True
    mocked_relay.assert_called_once()


def test_update_docker_app_can_disable_ldap(monkeypatch, tmp_path):
    compose_file = tmp_path / "docker-compose.yml"
    compose_file.write_text(
        "services:\n  app:\n    image: nginx:latest\n    container_name: docker-gate-myapp\n"
        "    extra_hosts: [host.docker.internal:host-gateway]\n"
        "    environment: {LDAP_HOST: host.docker.internal}\n"
    )
    entry = {
        "slug": "myapp", "image": "nginx:latest", "container_name": "docker-gate-myapp",
        "compose_project": "docker-gate-myapp", "compose_file": str(compose_file),
        "host_port": 9101, "ldap_enabled": True,
    }
    monkeypatch.setattr(dg, "_load_state", lambda: [entry])
    with patch.object(dg, "_run_docker_compose"), patch.object(dg, "ensure_ldap_relay") as mocked_relay:
        updated = dg.update_docker_app("myapp", image="nginx:latest", container_port=80, ldap_enabled=False)
    assert updated["ldap_enabled"] is False
    mocked_relay.assert_not_called()


def test_ensure_ldap_relay_skips_setup_when_already_active():
    active_status = MagicMock(stdout="active\n")
    with patch.object(dg.subprocess, "run", return_value=active_status) as mocked_run, \
            patch.object(dg, "_run_root_command") as mocked_root:
        dg.ensure_ldap_relay()
    mocked_run.assert_called_once()
    mocked_root.assert_not_called()


def test_ensure_ldap_relay_installs_and_starts_when_inactive(monkeypatch, tmp_path):
    inactive_status = MagicMock(stdout="inactive\n")
    monkeypatch.setattr(dg.shutil, "which", lambda name: "/usr/bin/socat")
    monkeypatch.setattr(dg, "_LDAP_RELAY_UNIT_TMP_PATH", tmp_path / "relay.service")
    with patch.object(dg.subprocess, "run", return_value=inactive_status), \
            patch.object(dg, "_run_root_command") as mocked_root:
        dg.ensure_ldap_relay()
    calls = [c.args[0] for c in mocked_root.call_args_list]
    assert calls[0] == ["cp", str(tmp_path / "relay.service"), str(dg._LDAP_RELAY_UNIT_PATH)]
    assert calls[1] == ["systemctl", "daemon-reload"]
    assert calls[2] == ["systemctl", "enable", "--now", dg._LDAP_RELAY_SERVICE_NAME]
    assert not (tmp_path / "relay.service").exists()


def test_ensure_ldap_relay_installs_socat_when_missing(monkeypatch, tmp_path):
    inactive_status = MagicMock(stdout="inactive\n")
    monkeypatch.setattr(dg.shutil, "which", lambda name: None)
    monkeypatch.setattr(dg, "_LDAP_RELAY_UNIT_TMP_PATH", tmp_path / "relay.service")
    with patch.object(dg.subprocess, "run", return_value=inactive_status), \
            patch.object(dg, "_run_root_command") as mocked_root:
        dg.ensure_ldap_relay()
    calls = [c.args[0] for c in mocked_root.call_args_list]
    assert calls[0] == ["apt-get", "install", "-y", "socat"]
