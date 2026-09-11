# Auteur : Patrick Ritaine
import pytest

import docker_gate as dg


def test_slug_is_valid_accepts_lowercase_alnum_dash():
    assert dg._slug_is_valid("my-app-2")


def test_slug_is_valid_rejects_uppercase():
    assert not dg._slug_is_valid("MyApp")


def test_slug_is_valid_rejects_single_char():
    assert not dg._slug_is_valid("a")


def test_slug_is_valid_rejects_leading_dash():
    assert not dg._slug_is_valid("-app")


def test_strip_port_protocol_removes_tcp_suffix():
    assert dg._strip_port_protocol("8080/tcp") == "8080"


def test_strip_port_protocol_no_suffix_unchanged():
    assert dg._strip_port_protocol("8080") == "8080"


def test_looks_like_spa_matches_known_image():
    assert dg._looks_like_spa("portainer/portainer-ce:latest")


def test_looks_like_spa_case_insensitive():
    assert dg._looks_like_spa("Dashy/Dashy")


def test_looks_like_spa_false_for_unknown_image():
    assert not dg._looks_like_spa("nginx:latest")


def test_looks_like_spa_false_for_none():
    assert not dg._looks_like_spa(None)


def test_build_create_steps_subdomain_mode_includes_domain_steps():
    steps = dg.build_create_steps("subdomain")
    assert "Creating domain" in steps
    assert "Getting certificate" in steps


def test_build_create_steps_path_mode_excludes_domain_steps():
    steps = dg.build_create_steps("path")
    assert "Creating domain" not in steps
    assert steps[0] == "Checking parameters"
    assert steps[-1] == "Exposing app"


def test_substitute_compose_vars_unresolved_left_as_is():
    text, unresolved = dg._substitute_compose_vars("${FOO}")
    assert text == "${FOO}"
    assert unresolved == ["FOO"]


def test_substitute_compose_vars_resolved_from_defaults():
    text, unresolved = dg._substitute_compose_vars("${FOO}", defaults={"FOO": "bar"})
    assert text == "bar"
    assert unresolved == []


def test_substitute_compose_vars_uses_inline_default():
    text, unresolved = dg._substitute_compose_vars("${FOO:-fallback}")
    assert text == "fallback"
    assert unresolved == []


def test_substitute_compose_vars_defaults_win_over_inline_default():
    text, unresolved = dg._substitute_compose_vars("${FOO:-fallback}", defaults={"FOO": "bar"})
    assert text == "bar"
    assert unresolved == []


def test_parse_env_vars_text_basic():
    env = dg.parse_env_vars_text("KEY1=value1\nKEY2=value2\n")
    assert env == {"KEY1": "value1", "KEY2": "value2"}


def test_parse_env_vars_text_skips_blank_and_comment_lines():
    env = dg.parse_env_vars_text("# comment\n\nKEY=value\n")
    assert env == {"KEY": "value"}


def test_parse_env_vars_text_rejects_line_without_equals():
    with pytest.raises(dg.DockerGateError):
        dg.parse_env_vars_text("not-a-valid-line")


def test_parse_docker_run_command_basic():
    result = dg.parse_docker_run_command("docker run -p 8080:80 -v /data:/app/data nginx:latest")
    assert result["image"] == "nginx:latest"
    assert result["container_port"] == "80"
    assert result["data_path"] == "/app/data"
    assert result["warnings"] == []


def test_parse_docker_run_command_extracts_name_as_slug():
    result = dg.parse_docker_run_command("docker run --name my-app nginx")
    assert result["suggested_slug"] == "my-app"


def test_parse_docker_run_command_multiple_ports_warns():
    result = dg.parse_docker_run_command("docker run -p 8080:80 -p 8081:81 nginx")
    assert result["container_port"] == "80"
    assert any("port" in w.lower() for w in result["warnings"])


def test_parse_docker_run_command_env_var_url_detected():
    result = dg.parse_docker_run_command("docker run -e APP_URL=https://example.com -e FOO=bar nginx")
    assert result["url_env_var"] == "APP_URL"
    assert result["env_vars"] == "FOO=bar"


def test_parse_docker_run_command_rejects_non_docker_text():
    with pytest.raises(dg.DockerGateError):
        dg.parse_docker_run_command("not a docker command")


def test_parse_docker_run_command_rejects_missing_run_subcommand():
    with pytest.raises(dg.DockerGateError):
        dg.parse_docker_run_command("docker ps -a")


def test_parse_docker_run_command_rejects_missing_image():
    with pytest.raises(dg.DockerGateError):
        dg.parse_docker_run_command("docker run -p 8080:80")


def test_parse_docker_run_command_handles_line_continuations():
    text = "docker run \\\n  -p 8080:80 \\\n  nginx:latest"
    result = dg.parse_docker_run_command(text)
    assert result["image"] == "nginx:latest"
    assert result["container_port"] == "80"


def test_extract_compose_service_fields_basic():
    service = {
        "image": "nginx:latest",
        "ports": ["8080:80"],
        "volumes": ["appdata:/app/data"],
        "environment": {"FOO": "bar"},
    }
    result, warnings = dg._extract_compose_service_fields(service, "web")
    assert result["image"] == "nginx:latest"
    assert result["container_port"] == "80"
    assert result["data_path"] == "/app/data"
    assert result["env_vars"] == "FOO=bar"
    assert warnings == []


def test_extract_compose_service_fields_skips_bind_mount_volumes():
    service = {"image": "nginx", "volumes": ["/host/path:/container/path"]}
    result, warnings = dg._extract_compose_service_fields(service, "web")
    assert result["data_path"] is None


def test_extract_compose_service_fields_detects_public_url_env_var():
    service = {"image": "app", "environment": {"APP_URL": "https://example.com"}}
    result, warnings = dg._extract_compose_service_fields(service, "web")
    assert result["url_env_var"] == "APP_URL"


def test_extract_compose_service_fields_ignores_internal_service_reference():
    service = {"image": "app", "environment": {"DB_URL": "http://database:5432"}}
    result, warnings = dg._extract_compose_service_fields(service, "web", sibling_service_keys={"database"})
    assert result["url_env_var"] is None
    assert result["env_vars"] == "DB_URL=http://database:5432"


def test_parse_compose_snippet_single_service():
    text = "image: nginx:latest\nports:\n  - \"8080:80\"\n"
    result = dg.parse_compose_snippet(text)
    assert result["image"] == "nginx:latest"
    assert result["container_port"] == "80"


def test_parse_compose_snippet_multi_service():
    text = (
        "services:\n"
        "  web:\n"
        "    image: nginx\n"
        "  db:\n"
        "    image: postgres\n"
    )
    result = dg.parse_compose_snippet(text)
    assert result["multi_service"] is True
    assert {s["image"] for s in result["services"]} == {"nginx", "postgres"}


def test_parse_compose_snippet_rejects_invalid_yaml():
    with pytest.raises(dg.DockerGateError):
        dg.parse_compose_snippet("services: [this is not: valid: yaml:")


def test_parse_compose_snippet_rejects_no_services():
    with pytest.raises(dg.DockerGateError):
        dg.parse_compose_snippet("services: {}")


def test_parse_compose_snippet_rejects_nothing_exploitable():
    with pytest.raises(dg.DockerGateError):
        dg.parse_compose_snippet("restart: always")


def test_autogenerate_secrets_replaces_password_placeholder():
    services = [{"service_key": "db", "env_vars": "DB_PASSWORD=changeme"}]
    generated = dg._autogenerate_secrets(services)
    assert len(generated) == 1
    assert "DB_PASSWORD" in generated[0]
    assert "changeme" not in services[0]["env_vars"]


def test_autogenerate_secrets_leaves_non_secret_vars_untouched():
    services = [{"service_key": "web", "env_vars": "FOO=bar"}]
    generated = dg._autogenerate_secrets(services)
    assert generated == []
    assert services[0]["env_vars"] == "FOO=bar"


def test_autogenerate_secrets_shares_replacement_across_services():
    services = [
        {"service_key": "web", "env_vars": "DB_PASSWORD=changeme"},
        {"service_key": "db", "env_vars": "DB_PASSWORD=changeme"},
    ]
    dg._autogenerate_secrets(services)
    web_value = services[0]["env_vars"].split("=", 1)[1]
    db_value = services[1]["env_vars"].split("=", 1)[1]
    assert web_value == db_value
    assert web_value != "changeme"


def test_smart_parse_input_rejects_empty():
    with pytest.raises(dg.DockerGateError):
        dg.smart_parse_input("   ")


def test_smart_parse_input_routes_docker_run_command():
    result = dg.smart_parse_input("docker run -p 80:80 nginx")
    assert result["image"] == "nginx"


def test_smart_parse_input_routes_compose_snippet():
    result = dg.smart_parse_input("image: nginx\nports:\n  - \"80:80\"\n")
    assert result["image"] == "nginx"


def test_smart_parse_input_flags_spa_image_for_subdomain_mode():
    result = dg.smart_parse_input("docker run --name p portainer/portainer-ce")
    assert result["suggested_mode"] == "subdomain"


def test_check_subdomain_status_invalid_name():
    status = dg.check_subdomain_status("Not Valid!", "byrtn.fr", lambda: [], lambda d: {})
    assert status["status"] == "invalid"


def test_check_subdomain_status_free():
    status = dg.check_subdomain_status("app", "byrtn.fr", lambda: [], lambda d: {})
    assert status == {"status": "free", "domain": "app.byrtn.fr"}


def test_check_subdomain_status_exists_used():
    status = dg.check_subdomain_status(
        "app", "byrtn.fr",
        lambda: ["app.byrtn.fr"],
        lambda d: {"apps": ["some_app"]},
    )
    assert status["status"] == "exists_used"
    assert status["suggestion"] == "app-2"


def test_check_subdomain_status_exists_empty():
    status = dg.check_subdomain_status(
        "app", "byrtn.fr",
        lambda: ["app.byrtn.fr"],
        lambda d: {"apps": []},
    )
    assert status["status"] == "exists_empty"


def test_check_path_status_invalid_path():
    status = dg.check_path_status("byrtn.fr", "not a valid path!", lambda: [])
    assert status["status"] == "invalid"


def test_check_path_status_free():
    status = dg.check_path_status("byrtn.fr", "/newapp", lambda: [])
    assert status["status"] == "free"


def test_check_path_status_used():
    apps = [{"domain_path": "byrtn.fr/existing", "name": "Existing App"}]
    status = dg.check_path_status("byrtn.fr", "/existing", lambda: apps)
    assert status["status"] == "used"
    assert status["app_name"] == "Existing App"


def test_check_path_status_normalizes_missing_leading_slash():
    status = dg.check_path_status("byrtn.fr", "newapp", lambda: [])
    assert status["path"] == "/newapp"
