from __future__ import annotations
# Auteur : Patrick Ritaine

import fcntl
import json
import os
import re
import secrets
import shlex
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.parse import urlencode

import requests
import yaml

import i18n

DATA_FILE = Path(__file__).parent / "data" / "docker_apps.json"
PORT_RANGE_START = 9100
PORT_RANGE_END = 9999

KNOWN_SPA_IMAGES = (
    "portainer", "dashy", "heimdall", "homepage", "homarr", "organizr", "flame",
)


def _t(key: str, lang: str, **kwargs) -> str:
    return i18n.t(key, i18n.normalize_lang(lang), **kwargs)


def _looks_like_spa(image):
    if not image:
        return False
    image_lower = image.lower()
    return any(name in image_lower for name in KNOWN_SPA_IMAGES)


_STATE_LOCK_FILE = Path(__file__).parent / "data" / "docker_port.lock"


class _CrossProcessLock:
    def __init__(self, blocking=True):
        self._blocking = blocking

    def __enter__(self):
        self._path = _STATE_LOCK_FILE
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = open(self._path, "w")
        flags = fcntl.LOCK_EX if self._blocking else fcntl.LOCK_EX | fcntl.LOCK_NB
        try:
            fcntl.flock(self._fh, flags)
        except OSError:
            self._fh.close()
            self._fh = None
            return None
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._fh is not None:
            fcntl.flock(self._fh, fcntl.LOCK_UN)
            self._fh.close()


def _state_lock():
    return _CrossProcessLock()


def _state_lock_nonblocking():
    return _CrossProcessLock(blocking=False)

_docker_client = None
_docker_client_error: str | None = None


class DockerGateError(Exception):
    pass


def _get_docker_client(lang: str = "en"):
    global _docker_client, _docker_client_error
    if _docker_client is not None:
        return _docker_client
    try:
        import docker
        _docker_client = docker.from_env()
        return _docker_client
    except Exception as e:
        _docker_client_error = str(e)
        raise DockerGateError(_t("dg_err_docker_daemon_unreachable", lang, detail=e))


def docker_available() -> bool:
    try:
        _get_docker_client()
        return True
    except DockerGateError:
        return False


def _load_state() -> list[dict]:
    if not DATA_FILE.exists():
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        corrupted_path = DATA_FILE.with_name(f"{DATA_FILE.name}.corrupted-{int(time.time())}")
        try:
            DATA_FILE.rename(corrupted_path)
        except OSError:
            pass
        return []


def _save_state(apps: list[dict]) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=DATA_FILE.parent, prefix=".apps-", suffix=".json.tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(apps, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, DATA_FILE)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _known_container_names(apps: list[dict]) -> set[str]:
    names = {a["container_name"] for a in apps if a.get("container_name")}
    names |= {c["container_name"] for a in apps for c in a.get("companions", []) if c.get("container_name")}
    return names


def list_apps(real_yunohost_app_ids: set[str] | None) -> list[dict]:
    apps = _load_state()

    for a in apps:
        if "visibility" not in a:
            a["visibility"] = "visitors" if a.get("public") else "admins"

    if real_yunohost_app_ids is not None:
        still_valid = [a for a in apps if not a.get("yunohost_app_id") or a["yunohost_app_id"] in real_yunohost_app_ids]
        if len(still_valid) != len(apps):
            with _state_lock_nonblocking() as lock:
                if lock is not None:
                    apps = _load_state()
                    still_valid = [
                        a for a in apps
                        if not a.get("yunohost_app_id") or a["yunohost_app_id"] in real_yunohost_app_ids
                    ]
                    if len(still_valid) != len(apps):
                        apps = still_valid
                        _save_state(apps)

    if docker_available():
        try:
            client = _get_docker_client()
            statuses = {c.name: c.status for c in client.containers.list(all=True)}
            for a in apps:
                container_name = a.get("container_name")
                status = statuses.get(container_name) if container_name else None
                a["container_status"] = status
                a["container_missing"] = bool(container_name) and status is None
        except DockerGateError:
            for a in apps:
                a["container_status"] = None
                a["container_missing"] = None
    else:
        for a in apps:
            a["container_status"] = None
            a["container_missing"] = None

    return apps


def _slug_is_valid(slug: str) -> bool:
    return bool(re.fullmatch(r"[a-z0-9][a-z0-9-]{1,30}", slug))


def _slug_already_used(slug: str) -> bool:
    return any(a["slug"] == slug for a in _load_state())


def _validate_cpu_limit(cpu_limit: str, lang: str = "en") -> str | None:
    cpu_limit = (cpu_limit or "").strip()
    if not cpu_limit:
        return None
    if not re.fullmatch(r"\d+(\.\d+)?", cpu_limit) or float(cpu_limit) <= 0:
        raise DockerGateError(_t("dg_err_cpu_limit_invalid", lang, value=cpu_limit))
    return cpu_limit


def _validate_mem_limit(mem_limit: str, lang: str = "en") -> str | None:
    mem_limit = (mem_limit or "").strip()
    if not mem_limit:
        return None
    if not re.fullmatch(r"\d+[mMgG]", mem_limit):
        raise DockerGateError(_t("dg_err_mem_limit_invalid", lang, value=mem_limit))
    return mem_limit


def _pick_free_port(lang: str = "en") -> int:
    used = {a["host_port"] for a in _load_state()}

    client = _get_docker_client(lang)
    for container in client.containers.list(all=True):
        for bindings in (container.ports or {}).values():
            if not bindings:
                continue
            for b in bindings:
                try:
                    used.add(int(b["HostPort"]))
                except (KeyError, ValueError, TypeError):
                    continue

    for port in range(PORT_RANGE_START, PORT_RANGE_END + 1):
        if port not in used:
            return port

    raise DockerGateError(_t("dg_err_no_free_port", lang))


def build_create_steps(mode: str, lang: str = "en") -> list[str]:
    steps = [_t("dg_step_check_parameters", lang), _t("dg_step_select_port", lang)]
    if mode == "subdomain":
        steps += [
            _t("dg_step_create_domain", lang),
            _t("dg_step_dns_diagnosis", lang),
            _t("dg_step_web_diagnosis", lang),
            _t("dg_step_get_certificate", lang),
            _t("dg_step_check_certificate", lang),
        ]
    steps += [_t("dg_step_write_configuration", lang), _t("dg_step_start_container", lang), _t("dg_step_expose_app", lang)]
    return steps


def build_edit_steps(lang: str = "en") -> list[str]:
    return [_t("dg_step_check_parameters", lang), _t("dg_step_write_configuration", lang), _t("dg_step_restart_container", lang)]


def fetch_compose_from_url(url: str, lang: str = "en") -> str:
    if not url.startswith("https://"):
        raise DockerGateError(_t("dg_err_https_only", lang))
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        raise DockerGateError(_t("dg_err_url_fetch_failed", lang, detail=e))
    if len(response.content) > 200_000:
        raise DockerGateError(_t("dg_err_file_too_large", lang))
    return response.text


_ENV_EXAMPLE_CANDIDATES = (".env.example", "example.env", ".env.sample", "env.example", ".env.dist", ".env.template")


def fetch_env_example_from_url(compose_url: str):
    if not compose_url.startswith("https://"):
        return None
    base = compose_url.rsplit("/", 1)[0] + "/"
    for name in _ENV_EXAMPLE_CANDIDATES:
        try:
            response = requests.get(base + name, timeout=5)
        except requests.RequestException:
            continue
        if response.status_code == 200 and 0 < len(response.content) <= 50_000 and response.text.strip():
            return response.text
    return None


_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
_LOGO_MAX_BYTES = 2_000_000


def fetch_catalogue_logo_bytes(url: str) -> bytes | None:
    if not url or not url.startswith("https://"):
        return None
    try:
        response = requests.get(url, timeout=10)
    except requests.RequestException:
        return None
    if response.status_code != 200:
        return None
    content = response.content
    if not content or len(content) > _LOGO_MAX_BYTES:
        return None
    if not content.startswith(_PNG_MAGIC):
        return None
    return content


def _strip_port_protocol(port_str: str) -> str:
    return port_str.split("/")[0]


def inspect_docker_image(image_name: str, lang: str = "en") -> dict:
    client = _get_docker_client(lang)
    import docker as docker_lib
    try:
        image = client.images.pull(image_name)
    except docker_lib.errors.APIError as e:
        raise DockerGateError(_t("dg_err_image_pull_failed", lang, image=image_name, detail=e))

    config = image.attrs.get("Config", {}) or {}
    result = {"image": image_name, "container_port": None, "data_path": None, "suggested_slug": None}

    exposed_ports = config.get("ExposedPorts") or {}
    if exposed_ports:
        result["container_port"] = _strip_port_protocol(next(iter(exposed_ports)))

    volumes = config.get("Volumes") or {}
    if volumes:
        result["data_path"] = next(iter(volumes))

    return result


_COMPOSE_VAR_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(:?[-?])?([^}]*)\}")


def _substitute_compose_vars(text, defaults=None):
    unresolved = []
    defaults = defaults or {}

    def _replace(match):
        name, operator, rest = match.group(1), match.group(2), match.group(3)
        if name in defaults:
            return defaults[name]
        if operator in (":-", "-"):
            return rest
        unresolved.append(name)
        return match.group(0)

    resolved_text = _COMPOSE_VAR_PATTERN.sub(_replace, text)
    return resolved_text, unresolved


def parse_docker_run_command(text: str, lang: str = "en") -> dict:
    joined = re.sub(r"\\\s*\n", " ", text)
    joined = joined.replace("\n", " ").strip()
    if not joined.startswith("docker "):
        raise DockerGateError(_t("dg_err_not_docker_run", lang))

    try:
        tokens = shlex.split(joined)
    except ValueError as e:
        raise DockerGateError(_t("dg_err_command_parse_failed", lang, detail=e))

    if "run" not in tokens:
        raise DockerGateError(_t("dg_err_no_run_subcommand", lang))

    tokens = tokens[tokens.index("run") + 1:]

    result = {"image": None, "container_port": None, "data_path": None, "env_vars": None, "url_env_var": None, "suggested_slug": None}
    warnings = []
    env_pairs = []
    i = 0
    image = None
    while i < len(tokens):
        tok = tokens[i]
        if tok == "--name" and i + 1 < len(tokens):
            result["suggested_slug"] = tokens[i + 1]
            i += 2
            continue
        if tok in ("-p", "--publish") and i + 1 < len(tokens):
            if result["container_port"] is None:
                result["container_port"] = _strip_port_protocol(tokens[i + 1].split(":")[-1])
            else:
                warnings.append(_t("dg_warn_multiple_published_ports", lang))
            i += 2
            continue
        if tok in ("-v", "--volume") and i + 1 < len(tokens):
            parts = tokens[i + 1].split(":")
            if len(parts) >= 2:
                if result["data_path"] is None:
                    result["data_path"] = parts[1]
                else:
                    warnings.append(_t("dg_warn_multiple_mounted_volumes", lang))
            i += 2
            continue
        if tok in ("-e", "--env") and i + 1 < len(tokens):
            k, _, v = tokens[i + 1].partition("=")
            env_pairs.append((k.strip(), v.strip()))
            i += 2
            continue
        if tok.startswith("-"):
            if i + 1 < len(tokens) and not tokens[i + 1].startswith("-") and i + 1 != len(tokens) - 1:
                i += 2
            else:
                i += 1
            continue
        image = tok
        i += 1

    if image:
        result["image"] = image

    other_lines = []
    for key, value in env_pairs:
        if not result["url_env_var"] and re.match(r"^https?://", value):
            result["url_env_var"] = key
        else:
            other_lines.append(f"{key}={value}")
    if other_lines:
        result["env_vars"] = "\n".join(other_lines)

    if not result["image"]:
        raise DockerGateError(_t("dg_err_no_docker_image_found", lang))

    result["warnings"] = warnings
    return result


def smart_parse_input(text: str, env_example_text=None, lang: str = "en") -> dict:
    stripped = text.strip()
    if not stripped:
        raise DockerGateError(_t("dg_err_nothing_to_parse", lang))

    if stripped.startswith("docker "):
        result = parse_docker_run_command(stripped, lang=lang)
    elif "\n" in stripped or stripped.lstrip().startswith(("services:", "image:")):
        result = parse_compose_snippet(stripped, env_example_text=env_example_text, lang=lang)
    elif re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._/-]*(:[a-zA-Z0-9._-]+)?", stripped):
        result = inspect_docker_image(stripped, lang=lang)
    else:
        raise DockerGateError(_t("dg_err_unrecognized_format", lang))

    if result.get("multi_service"):
        for service_result in result["services"]:
            if _looks_like_spa(service_result.get("image")):
                service_result["suggested_mode"] = "subdomain"
    elif _looks_like_spa(result.get("image")):
        result["suggested_mode"] = "subdomain"
    result.setdefault("warnings", [])
    return result


def _is_internal_service_reference(url_value, sibling_service_keys):
    if not sibling_service_keys:
        return False
    try:
        host = url_value.split("://", 1)[1].split("/")[0].split(":")[0]
    except IndexError:
        return False
    return host in sibling_service_keys


def _extract_compose_service_fields(service, service_key, sibling_service_keys=None, env_example_vars=None, lang: str = "en"):
    result = {"image": None, "container_port": None, "data_path": None, "env_vars": None, "url_env_var": None,
              "service_key": service_key,
              "suggested_slug": service.get("container_name") or service_key}
    warnings = []
    pairs = []

    if service.get("env_file"):
        if env_example_vars:
            pairs.extend(env_example_vars.items())
        else:
            warnings.append(_t("dg_warn_env_file_unsupported", lang))

    if "image" in service:
        result["image"] = str(service["image"])

    ports = service.get("ports")
    if ports and isinstance(ports, list) and ports:
        first = str(ports[0])
        result["container_port"] = _strip_port_protocol(first.split(":")[-1])
        if len(ports) > 1:
            warnings.append(_t("dg_warn_multiple_declared_ports", lang))

    volumes = service.get("volumes")
    if volumes and isinstance(volumes, list):
        candidates_found = 0
        for v in volumes:
            v_str = str(v)
            parts = v_str.split(":")
            if len(parts) < 2:
                continue
            source = parts[0]
            if source.startswith("/"):
                continue
            candidates_found += 1
            if result["data_path"] is None:
                result["data_path"] = parts[1]
        if candidates_found > 1:
            warnings.append(_t("dg_warn_multiple_declared_volumes", lang))

    environment = service.get("environment")
    if environment:
        if isinstance(environment, list):
            for e in environment:
                k, _, v = str(e).partition("=")
                pairs.append((k.strip(), v.strip()))
        elif isinstance(environment, dict):
            pairs.extend((str(k), str(v)) for k, v in environment.items())

    if pairs:
        merged = dict(pairs)
        other_lines = []
        for key, value in merged.items():
            if (not result["url_env_var"] and re.match(r"^https?://", value)
                    and not _is_internal_service_reference(value, sibling_service_keys)):
                result["url_env_var"] = key
            else:
                other_lines.append(f"{key}={value}")
        if other_lines:
            result["env_vars"] = "\n".join(other_lines)

    return result, warnings


_SECRET_KEY_RE = re.compile(r"(PASSWORD|PASSWD|SECRET|TOKEN|_KEY)$")


def _autogenerate_secrets(parsed_services):
    replacements = {}
    generated_labels = []
    for service in parsed_services:
        if not service.get("env_vars"):
            continue
        new_lines = []
        for line in service["env_vars"].splitlines():
            key, sep, value = line.partition("=")
            if sep and value and value not in replacements and _SECRET_KEY_RE.search(key.strip().upper()):
                new_value = secrets.token_urlsafe(24)
                replacements[value] = new_value
                generated_labels.append(f"{key.strip()} ({service.get('service_key') or '?'})")
                new_lines.append(f"{key}={new_value}")
            else:
                new_lines.append(line)
        service["env_vars"] = "\n".join(new_lines)

    if not replacements:
        return []

    for service in parsed_services:
        if not service.get("env_vars"):
            continue
        new_lines = []
        for line in service["env_vars"].splitlines():
            key, sep, value = line.partition("=")
            if sep and value in replacements and _SECRET_KEY_RE.search(key.strip().upper()):
                new_lines.append(f"{key}={replacements[value]}")
            else:
                new_lines.append(line)
        service["env_vars"] = "\n".join(new_lines)

    return generated_labels


def parse_compose_snippet(text: str, env_example_text=None, lang: str = "en") -> dict:
    env_example_vars = None
    if env_example_text:
        try:
            env_example_vars = parse_env_vars_text(env_example_text, lang=lang)
        except DockerGateError:
            pass

    text, unresolved_vars = _substitute_compose_vars(text, defaults=env_example_vars)

    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as e:
        raise DockerGateError(_t("dg_err_compose_invalid", lang, detail=e))

    if not isinstance(data, dict):
        raise DockerGateError(_t("dg_err_compose_not_valid_content", lang))

    if "services" in data and isinstance(data["services"], dict):
        services = data["services"]
        if not services:
            raise DockerGateError(_t("dg_err_no_service_found", lang))
    else:
        services = {None: data}

    compose_warnings = []
    if unresolved_vars:
        compose_warnings.append(_t("dg_warn_unresolved_vars", lang, names=", ".join(sorted(set(unresolved_vars)))))

    if len(services) > 1:
        all_service_keys = set(services.keys())
        parsed_services = []
        env_example_applied = False
        for service_key, service in services.items():
            if not isinstance(service, dict):
                raise DockerGateError(_t("dg_err_unrecognized_service_format", lang))
            sibling_keys = all_service_keys - {service_key}
            if env_example_vars and service.get("env_file"):
                env_example_applied = True
            service_result, service_warnings = _extract_compose_service_fields(
                service, service_key, sibling_keys, env_example_vars=env_example_vars, lang=lang)
            service_result["warnings"] = service_warnings
            parsed_services.append(service_result)
        if not any(s["image"] for s in parsed_services):
            raise DockerGateError(_t("dg_err_no_image_found_compose", lang))
        if env_example_applied:
            compose_warnings.append(_t("dg_warn_env_example_used", lang))
        generated = _autogenerate_secrets(parsed_services)
        if generated:
            compose_warnings.append(_t("dg_warn_secrets_autogenerated", lang, names=", ".join(generated)))
        return {"multi_service": True, "services": parsed_services, "warnings": compose_warnings}

    service_key, service = next(iter(services.items()))
    if not isinstance(service, dict):
        raise DockerGateError(_t("dg_err_unrecognized_service_format", lang))

    result, service_warnings = _extract_compose_service_fields(service, service_key, env_example_vars=env_example_vars, lang=lang)
    if env_example_vars and service.get("env_file"):
        compose_warnings.append(_t("dg_warn_env_example_used", lang))

    if not result["image"] and not result["container_port"] and not result["data_path"] and not result["env_vars"]:
        raise DockerGateError(_t("dg_err_nothing_usable_in_compose", lang))

    result["warnings"] = compose_warnings + service_warnings
    return result


def parse_env_vars_text(text: str, lang: str = "en") -> dict:
    env = {}
    for i, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise DockerGateError(_t("dg_err_invalid_line_no_equals", lang, line_num=i, line=line))
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip()
    return env


def _compose_dir(slug: str) -> Path:
    return Path(__file__).parent / "data" / "compose" / slug


_CONFIG_FILE_NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")


def _write_bind_mount_file(slug: str, relative_name: str, content: str, lang: str = "en") -> None:
    if not _CONFIG_FILE_NAME_RE.fullmatch(relative_name or ""):
        raise DockerGateError(_t("dg_err_invalid_config_filename", lang, name=relative_name))
    config_dir = _compose_dir(slug) / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / relative_name).write_text(content)


def _build_compose_document(slug, main_key, image, container_port, host_port, env_vars, data_path, companions,
                             config_files=None, cpu_limit=None, mem_limit=None, ldap_enabled=False):
    services = {}
    volumes = {}

    main_service = {
        "image": image,
        "container_name": f"docker-gate-{slug}",
        "restart": "unless-stopped",
        "ports": [f"127.0.0.1:{host_port}:{container_port}/tcp"],
    }
    merged_env_vars = dict(env_vars) if env_vars else {}
    if ldap_enabled:
        merged_env_vars.update(ldap_env_vars())
    if merged_env_vars:
        main_service["environment"] = merged_env_vars
    _apply_ldap_wiring(main_service, ldap_enabled)
    if cpu_limit:
        main_service["cpus"] = cpu_limit
    if mem_limit:
        main_service["mem_limit"] = mem_limit
    main_volumes = []
    if data_path:
        volume_name = f"docker-gate-{slug}-data"
        volumes[volume_name] = {"name": volume_name}
        main_volumes.append(f"{volume_name}:{data_path}")
    for cf in config_files or []:
        main_volumes.append(f"./config/{cf['host_relative_path']}:{cf['container_path']}:ro")
    if main_volumes:
        main_service["volumes"] = main_volumes
    if companions:
        main_service["depends_on"] = [c["service_key"] for c in companions]
    services[main_key] = main_service

    for c in companions:
        service_key = c["service_key"]
        companion_service = {
            "image": c["image"],
            "container_name": f"docker-gate-{slug}-{service_key}",
            "restart": "unless-stopped",
        }
        if c.get("env_vars"):
            companion_service["environment"] = c["env_vars"]
        if c.get("data_path"):
            volume_name = f"docker-gate-{slug}-{service_key}-data"
            volumes[volume_name] = {"name": volume_name}
            companion_service["volumes"] = [f"{volume_name}:{c['data_path']}"]
        services[service_key] = companion_service

    doc = {"services": services, "networks": {"default": {"name": f"docker-gate-{slug}-net"}}}
    if volumes:
        doc["volumes"] = volumes
    return doc


def _run_docker_compose(project_name, compose_path, args, error_message, timeout=180, lang: str = "en"):
    try:
        result = subprocess.run(
            ["docker", "compose", "-p", project_name, "-f", str(compose_path)] + args,
            capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise DockerGateError(_t("dg_err_timeout_after", lang, message=error_message, timeout=timeout))
    if result.returncode != 0:
        raise DockerGateError(_t("dg_err_with_detail", lang, message=error_message, detail=(result.stderr.strip() or result.stdout.strip())))
    return result.stdout


def _teardown_compose_project(project_name, compose_path):
    try:
        subprocess.run(
            ["docker", "compose", "-p", project_name, "-f", str(compose_path), "down", "-v"],
            capture_output=True, text=True, timeout=180,
        )
    except (subprocess.TimeoutExpired, OSError):
        pass


def check_subdomain_status(new_subdomain, domain_parent, existing_domains_fn, domain_detail_fn):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,62}", new_subdomain or ""):
        return {"status": "invalid"}

    target_domain = f"{new_subdomain}.{domain_parent}"
    domains = existing_domains_fn()

    if target_domain not in domains:
        return {"status": "free", "domain": target_domain}

    try:
        info = domain_detail_fn(target_domain)
        apps_on_domain = info.get("apps", [])
    except Exception:
        apps_on_domain = ["?"]

    if apps_on_domain:
        return {"status": "exists_used", "domain": target_domain, "suggestion": f"{new_subdomain}-2"}

    return {"status": "exists_empty", "domain": target_domain}


def check_path_status(domain, path, list_apps_fn):
    normalized_path = path if path.startswith("/") else f"/{path}"
    if not re.fullmatch(r"/[a-zA-Z0-9._~-]*(?:/[a-zA-Z0-9._~-]+)*", normalized_path):
        return {"status": "invalid"}

    apps = list_apps_fn()
    target = f"{domain}{normalized_path}".rstrip("/")

    for a in apps:
        existing = (a.get("domain_path") or "").rstrip("/")
        if existing == target:
            return {"status": "used", "domain": domain, "path": normalized_path, "app_name": a.get("name")}

    return {"status": "free", "domain": domain, "path": normalized_path}


def resolve_target_url(mode, domain, domain_parent, path, new_subdomain, lang: str = "en"):
    if mode == "subdomain":
        if not new_subdomain or not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,62}", new_subdomain):
            raise DockerGateError(_t("dg_err_invalid_subdomain", lang))
        if not domain_parent:
            raise DockerGateError(_t("dg_err_missing_parent_domain", lang))
        return f"https://{new_subdomain}.{domain_parent}/"

    if not domain:
        raise DockerGateError(_t("dg_err_missing_domain", lang))
    normalized_path = path if path.startswith("/") else f"/{path}"
    if not re.fullmatch(r"/[a-zA-Z0-9._~-]*(?:/[a-zA-Z0-9._~-]+)*", normalized_path):
        raise DockerGateError(_t("dg_err_invalid_path", lang))
    return f"https://{domain}{normalized_path}"


_CATALOGUE_URL = "https://raw.githubusercontent.com/Lissy93/portainer-templates/main/templates.json"
_CATALOGUE_CACHE_FILE = Path(__file__).parent / "data" / "docker_catalogue_cache.json"
_CATALOGUE_CACHE_TTL_SECONDS = 86400

_KNOWN_GOOD_ENV_OVERRIDES = {
    "ghost": {
        "database__client": "sqlite3",
        "database__connection__filename": "/var/lib/ghost/content/data/ghost.db",
    },
}


def _base_image_name(image: str) -> str:
    without_tag = (image or "").split("@")[0].split(":")[0]
    return without_tag.rsplit("/", 1)[-1]


def _normalize_catalogue_entry(t: dict) -> dict | None:
    if t.get("type") != 1 or not t.get("image"):
        return None

    container_port = None
    port_field = t.get("ports")
    if port_field and isinstance(port_field, list) and port_field:
        first = str(port_field[0])
        container_side = first.split(":")[-1]
        container_port = _strip_port_protocol(container_side)

    data_path = None
    volumes_field = t.get("volumes")
    if volumes_field and isinstance(volumes_field, list) and volumes_field:
        data_path = volumes_field[0].get("container")

    env_vars = {}
    for e in t.get("env") or []:
        name = e.get("name")
        default = e.get("default")
        if name and default not in (None, ""):
            env_vars[name] = str(default)
    env_vars.update(_KNOWN_GOOD_ENV_OVERRIDES.get(_base_image_name(t.get("image")), {}))

    return {
        "title": t.get("title") or t.get("name") or t.get("image"),
        "description": (t.get("description") or "").strip(),
        "image": t.get("image"),
        "logo": t.get("logo"),
        "categories": t.get("categories") or [],
        "container_port": container_port,
        "data_path": data_path,
        "env_vars": env_vars,
    }


def _fetch_catalogue_live() -> list[dict]:
    response = requests.get(_CATALOGUE_URL, timeout=15)
    response.raise_for_status()
    data = response.json()
    entries = []
    for t in data.get("templates", []):
        entry = _normalize_catalogue_entry(t)
        if entry and entry["image"]:
            entries.append(entry)
    return entries


def fetch_app_catalogue(force_refresh: bool = False) -> dict:
    cached = None
    if _CATALOGUE_CACHE_FILE.is_file():
        try:
            cached = json.loads(_CATALOGUE_CACHE_FILE.read_text())
        except (OSError, ValueError):
            cached = None

    if not force_refresh and cached and (time.time() - cached.get("fetched_at", 0)) < _CATALOGUE_CACHE_TTL_SECONDS:
        return {"apps": cached["apps"], "source": "cache", "fetched_at": cached["fetched_at"]}

    try:
        apps = _fetch_catalogue_live()
    except (requests.RequestException, ValueError) as e:
        if cached:
            return {"apps": cached["apps"], "source": "stale_cache", "fetched_at": cached["fetched_at"]}
        return {"apps": [], "source": "unavailable", "fetched_at": None, "error": str(e)}

    fetched_at = time.time()
    _CATALOGUE_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = _CATALOGUE_CACHE_FILE.with_suffix(".tmp")
    tmp_path.write_text(json.dumps({"apps": apps, "fetched_at": fetched_at}))
    os.replace(tmp_path, _CATALOGUE_CACHE_FILE)
    return {"apps": apps, "source": "live", "fetched_at": fetched_at}


def create_docker_app(
    slug, image, container_port, mode, domain, domain_parent, path, new_subdomain, visibility,
    data_path="", env_vars=None, url_env_var="", reuse_existing_domain=False,
    companions=None, main_service_key=None, config_files=None, cpu_limit="", mem_limit="",
    ldap_enabled=False, logo_bytes=None, on_step=None, lang: str = "en",
    *,
    add_domain_fn, run_diagnosis_fn, install_cert_fn, domain_detail_fn,
    install_app_fn, list_app_ids_fn, set_permission_logo_fn=None,
):
    warnings = []

    def step(label):
        if on_step:
            on_step(label)

    step(_t("dg_step_check_parameters", lang))
    if not _slug_is_valid(slug):
        raise DockerGateError(_t("dg_err_invalid_slug", lang))
    if _slug_already_used(slug):
        raise DockerGateError(_t("dg_err_slug_already_used", lang, slug=slug))

    try:
        container_port = int(container_port)
    except (TypeError, ValueError):
        raise DockerGateError(_t("dg_err_container_port_must_be_number", lang))

    cpu_limit = _validate_cpu_limit(cpu_limit, lang=lang)
    mem_limit = _validate_mem_limit(mem_limit, lang=lang)

    if mode == "subdomain":
        if not new_subdomain or not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,62}", new_subdomain):
            raise DockerGateError(_t("dg_err_invalid_subdomain", lang))
        if not domain_parent:
            raise DockerGateError(_t("dg_err_missing_parent_domain", lang))
        target_domain = f"{new_subdomain}.{domain_parent}"
        target_path = "/"
    else:
        if not domain:
            raise DockerGateError(_t("dg_err_missing_domain", lang))
        normalized_path = path if path.startswith("/") else f"/{path}"
        if not re.fullmatch(r"/[a-zA-Z0-9._~-]*(?:/[a-zA-Z0-9._~-]+)*", normalized_path):
            raise DockerGateError(_t("dg_err_invalid_path", lang))
        target_domain = domain
        target_path = normalized_path

    permission_group = visibility if visibility in ("admins", "all_users", "visitors") else "admins"

    with _state_lock():
        step(_t("dg_step_select_port", lang))
        host_port = _pick_free_port(lang=lang)

        if mode == "subdomain":
            if not reuse_existing_domain:
                step(_t("dg_step_create_domain", lang))
                add_domain_fn(target_domain)

            step(_t("dg_step_dns_diagnosis", lang))
            if not run_diagnosis_fn("dnsrecords"):
                warnings.append(_t("dg_warn_dns_diagnosis_unverified", lang, domain=target_domain))

            step(_t("dg_step_web_diagnosis", lang))
            if not run_diagnosis_fn("web"):
                warnings.append(_t("dg_warn_web_diagnosis_unverified", lang, domain=target_domain))

            step(_t("dg_step_get_certificate", lang))
            try:
                install_cert_fn(target_domain)
            except Exception:
                pass

            step(_t("dg_step_check_certificate", lang))
            ca_type = None
            try:
                detail = domain_detail_fn(target_domain)
                ca_type = (detail.get("certificate") or {}).get("CA_type")
            except Exception as e:
                warnings.append(_t("dg_warn_cert_check_failed", lang, domain=target_domain, detail=e))

            if ca_type and ca_type != "letsencrypt":
                warnings.append(_t("dg_warn_cert_not_letsencrypt", lang, domain=target_domain, ca_type=ca_type))

        if url_env_var:
            env_vars = dict(env_vars) if env_vars else {}
            if target_path == "/":
                env_vars[url_env_var] = f"https://{target_domain}/"
            else:
                env_vars[url_env_var] = f"https://{target_domain}{target_path}"

        main_key = main_service_key or "app"
        project_name = f"docker-gate-{slug}"
        compose_path = _compose_dir(slug) / "docker-compose.yml"

        step(_t("dg_step_write_configuration", lang))
        if ldap_enabled:
            ensure_ldap_relay(lang=lang)
        resolved_config_files = []
        for cf in config_files or []:
            container_path = (cf.get("container_path") or "").strip()
            filename = (cf.get("filename") or "").strip()
            if not container_path.startswith("/"):
                raise DockerGateError(_t("dg_err_invalid_config_file_path", lang, path=container_path))
            _write_bind_mount_file(slug, filename, cf.get("content") or "", lang=lang)
            resolved_config_files.append({"container_path": container_path, "host_relative_path": filename})

        compose_doc = _build_compose_document(
            slug=slug, main_key=main_key, image=image, container_port=container_port,
            host_port=host_port, env_vars=env_vars, data_path=data_path, companions=companions or [],
            config_files=resolved_config_files, cpu_limit=cpu_limit, mem_limit=mem_limit,
            ldap_enabled=ldap_enabled,
        )
        try:
            compose_path.parent.mkdir(parents=True, exist_ok=True)
            with open(compose_path, "w") as f:
                yaml.safe_dump(compose_doc, f, sort_keys=False)
        except OSError as e:
            raise DockerGateError(_t("dg_err_write_config_failed", lang, detail=e))

        step(_t("dg_step_start_container", lang))
        _run_docker_compose(project_name, compose_path, ["config", "-q"], _t("dg_err_invalid_configuration", lang), timeout=30, lang=lang)
        try:
            _run_docker_compose(
                project_name, compose_path,
                ["up", "-d", "--wait", "--wait-timeout", "120", "--pull", "missing"],
                _t("dg_err_container_start_failed", lang), timeout=240, lang=lang,
            )
        except DockerGateError:
            _teardown_compose_project(project_name, compose_path)
            raise


    container_name = f"docker-gate-{slug}"
    volume_name = f"docker-gate-{slug}-data" if data_path else None
    network_name = f"docker-gate-{slug}-net"
    companion_entries = [
        {
            "service_key": c["service_key"],
            "container_name": f"docker-gate-{slug}-{c['service_key']}",
            "image": c["image"],
            "volume_name": f"docker-gate-{slug}-{c['service_key']}-data" if c.get("data_path") else None,
            "data_path": c.get("data_path"),
            "env_var_keys": sorted(c["env_vars"].keys()) if c.get("env_vars") else [],
        }
        for c in (companions or [])
    ]

    step(_t("dg_step_expose_app", lang))
    args_string = urlencode({
        "domain": target_domain,
        "path": target_path,
        "redirect_type": "reverseproxy",
        "target": f"http://127.0.0.1:{host_port}",
        "init_main_permission": permission_group,
    })

    apps_before = list_app_ids_fn()
    try:
        install_app_fn("redirect", slug, args_string)
    except Exception:
        _teardown_compose_project(project_name, compose_path)
        raise
    apps_after = list_app_ids_fn()
    new_app_ids = apps_after - apps_before
    yunohost_app_id = next(iter(new_app_ids), None)

    if yunohost_app_id and logo_bytes and set_permission_logo_fn:
        try:
            set_permission_logo_fn(f"{yunohost_app_id}.main", "logo.png", logo_bytes)
        except Exception as e:
            warnings.append(_t("dg_warn_logo_not_applied", lang, detail=e))

    entry = {
        "slug": slug,
        "image": image,
        "container_name": container_name,
        "container_port": container_port,
        "host_port": host_port,
        "domain": target_domain,
        "path": target_path,
        "mode": mode,
        "visibility": permission_group,
        "yunohost_app_id": yunohost_app_id,
        "volume_name": volume_name,
        "data_path": data_path or None,
        "env_var_keys": sorted(env_vars.keys()) if env_vars else [],
        "network_name": network_name,
        "companions": companion_entries,
        "config_files": resolved_config_files,
        "cpu_limit": cpu_limit,
        "mem_limit": mem_limit,
        "ldap_enabled": bool(ldap_enabled),
        "compose_project": project_name,
        "compose_file": str(compose_path),
    }
    apps = _load_state()
    apps.append(entry)
    _save_state(apps)
    entry["warnings"] = warnings
    return entry


def _find_entry(slug: str, lang: str = "en") -> tuple[list[dict], dict]:
    apps = _load_state()
    entry = next((a for a in apps if a["slug"] == slug), None)
    if entry is None:
        raise DockerGateError(_t("dg_err_unknown_app", lang, slug=slug))
    return apps, entry


def get_app_entry(slug: str, lang: str = "en") -> dict:
    _, entry = _find_entry(slug, lang=lang)
    return entry


def get_app_entry_by_yunohost_id(yunohost_app_id: str) -> dict | None:
    apps = _load_state()
    return next((a for a in apps if a.get("yunohost_app_id") == yunohost_app_id), None)


def get_all_yunohost_app_ids() -> set[str]:
    apps = _load_state()
    return {a["yunohost_app_id"] for a in apps if a.get("yunohost_app_id")}


def _find_main_service_key(doc: dict, container_name: str, lang: str = "en") -> str:
    services = doc.get("services", {})
    for key, service in services.items():
        if service.get("container_name") == container_name:
            return key
    if services:
        return next(iter(services))
    raise DockerGateError(_t("dg_err_no_service_in_container_config", lang))


def read_current_env_vars(slug: str) -> dict:
    _, entry = _find_entry(slug)
    compose_file = entry.get("compose_file")
    if not compose_file or not Path(compose_file).exists():
        return {}
    doc = yaml.safe_load(Path(compose_file).read_text()) or {}
    main_key = _find_main_service_key(doc, entry.get("container_name"))
    return doc.get("services", {}).get(main_key, {}).get("environment") or {}


def update_docker_app(slug, image, container_port, data_path="", env_vars=None, cpu_limit="", mem_limit="",
                       ldap_enabled=None, on_step=None, lang: str = "en"):
    with _state_lock():
        return _update_docker_app_locked(
            slug, image, container_port, data_path=data_path, env_vars=env_vars, cpu_limit=cpu_limit,
            mem_limit=mem_limit, ldap_enabled=ldap_enabled, on_step=on_step, lang=lang,
        )


def _update_docker_app_locked(slug, image, container_port, data_path="", env_vars=None, cpu_limit="", mem_limit="",
                               ldap_enabled=None, on_step=None, lang: str = "en"):
    warnings = []

    def step(label):
        if on_step:
            on_step(label)

    step(_t("dg_step_check_parameters", lang))
    apps, entry = _find_entry(slug, lang=lang)

    compose_file = entry.get("compose_file")
    if not compose_file or not Path(compose_file).exists():
        raise DockerGateError(_t("dg_err_compose_file_not_found", lang))

    image = (image or "").strip()
    if not image:
        raise DockerGateError(_t("dg_err_image_required", lang))
    try:
        container_port = int(container_port)
    except (TypeError, ValueError):
        raise DockerGateError(_t("dg_err_container_port_must_be_number", lang))
    cpu_limit = _validate_cpu_limit(cpu_limit, lang=lang)
    mem_limit = _validate_mem_limit(mem_limit, lang=lang)
    data_path = (data_path or "").strip()

    compose_path = Path(compose_file)
    doc = yaml.safe_load(compose_path.read_text()) or {}
    main_key = _find_main_service_key(doc, entry.get("container_name"), lang=lang)
    main_service = doc["services"][main_key]

    step(_t("dg_step_write_configuration", lang))
    main_service["image"] = image
    main_service["ports"] = [f"127.0.0.1:{entry['host_port']}:{container_port}/tcp"]
    effective_ldap_enabled = entry.get("ldap_enabled", False) if ldap_enabled is None else bool(ldap_enabled)
    merged_env_vars = dict(env_vars) if env_vars else {}
    if effective_ldap_enabled:
        merged_env_vars.update(ldap_env_vars())
    if merged_env_vars:
        main_service["environment"] = merged_env_vars
    else:
        main_service.pop("environment", None)
    _apply_ldap_wiring(main_service, effective_ldap_enabled)
    if cpu_limit:
        main_service["cpus"] = cpu_limit
    else:
        main_service.pop("cpus", None)
    if mem_limit:
        main_service["mem_limit"] = mem_limit
    else:
        main_service.pop("mem_limit", None)

    config_volumes = [v for v in (main_service.get("volumes") or []) if v.startswith("./config/")]
    volume_name = f"docker-gate-{slug}-data"
    doc_volumes = doc.setdefault("volumes", {})
    if data_path:
        doc_volumes[volume_name] = {"name": volume_name}
        main_service["volumes"] = [f"{volume_name}:{data_path}"] + config_volumes
    else:
        doc_volumes.pop(volume_name, None)
        if config_volumes:
            main_service["volumes"] = config_volumes
        else:
            main_service.pop("volumes", None)
    if not doc_volumes:
        doc.pop("volumes", None)

    try:
        with open(compose_path, "w") as f:
            yaml.safe_dump(doc, f, sort_keys=False)
    except OSError as e:
        raise DockerGateError(_t("dg_err_write_config_failed", lang, detail=e))

    if effective_ldap_enabled:
        ensure_ldap_relay(lang=lang)

    step(_t("dg_step_restart_container", lang))
    _run_docker_compose(entry["compose_project"], compose_path, ["config", "-q"], _t("dg_err_invalid_configuration", lang), timeout=30, lang=lang)
    _run_docker_compose(
        entry["compose_project"], compose_path,
        ["up", "-d", "--wait", "--wait-timeout", "120"],
        _t("dg_err_container_update_failed", lang), timeout=180, lang=lang,
    )

    entry["image"] = image
    entry["container_port"] = container_port
    entry["data_path"] = data_path or None
    entry["volume_name"] = volume_name if data_path else None
    entry["env_var_keys"] = sorted(env_vars.keys()) if env_vars else []
    entry["cpu_limit"] = cpu_limit
    entry["mem_limit"] = mem_limit
    entry["ldap_enabled"] = effective_ldap_enabled
    _save_state(apps)
    entry["warnings"] = warnings
    return entry


def update_docker_app_url(slug: str, domain: str, path: str) -> dict:
    with _state_lock():
        apps, entry = _find_entry(slug)
        entry["domain"] = domain
        entry["path"] = path
        _save_state(apps)
        return entry


def _remove_stale_app_logo(yunohost_app_id: str) -> None:
    if not re.fullmatch(r"redirect__\d+", yunohost_app_id or ""):
        return
    logo_path = f"/usr/share/yunohost/applogos/{yunohost_app_id}.png"
    try:
        subprocess.run(["sudo", "-n", "rm", "-f", logo_path], capture_output=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        pass


def remove_docker_app(slug, delete_data=False, delete_domain=False, lang: str = "en", *, remove_app_fn, remove_domain_fn=None):
    with _state_lock():
        return _remove_docker_app_locked(
            slug, delete_data=delete_data, delete_domain=delete_domain, lang=lang,
            remove_app_fn=remove_app_fn, remove_domain_fn=remove_domain_fn,
        )


def _remove_docker_app_locked(slug, delete_data=False, delete_domain=False, lang: str = "en", *, remove_app_fn, remove_domain_fn=None):
    apps = _load_state()
    entry = next((a for a in apps if a["slug"] == slug), None)
    if entry is None:
        raise DockerGateError(_t("dg_err_unknown_app", lang, slug=slug))

    warnings = []

    if entry.get("yunohost_app_id"):
        try:
            remove_app_fn(entry["yunohost_app_id"])
        except Exception as e:
            warnings.append(_t("dg_warn_yunohost_exposure_removal_failed", lang, detail=e))
        _remove_stale_app_logo(entry["yunohost_app_id"])

    if entry.get("compose_project"):
        compose_file = Path(entry["compose_file"]) if entry.get("compose_file") else None
        down_args = ["down", "-v", "--rmi", "all"] if delete_data else ["down"]
        try:
            if compose_file and compose_file.exists():
                _run_docker_compose(entry["compose_project"], compose_file, down_args, _t("dg_err_container_stop_failed", lang), lang=lang)
            else:
                result = subprocess.run(
                    ["docker", "compose", "-p", entry["compose_project"]] + down_args,
                    capture_output=True, text=True, timeout=180,
                )
                if result.returncode != 0:
                    raise DockerGateError(_t("dg_err_container_stop_failed_detail", lang, detail=result.stderr.strip()))
        except (DockerGateError, subprocess.TimeoutExpired) as e:
            warnings.append(str(e))
        if compose_file and compose_file.parent.exists():
            try:
                shutil.rmtree(compose_file.parent)
            except OSError:
                pass

    if delete_domain and entry.get("mode") == "subdomain" and remove_domain_fn:
        try:
            remove_domain_fn(entry["domain"])
        except Exception as e:
            warnings.append(_t("dg_warn_domain_removal_failed", lang, detail=e))

    apps = [a for a in apps if a["slug"] != slug]
    _save_state(apps)

    return warnings


_CONTAINER_ACTIONS = ("start", "stop", "restart")


def container_action(slug: str, action: str, lang: str = "en") -> None:
    if action not in _CONTAINER_ACTIONS:
        raise DockerGateError(_t("dg_err_unknown_action", lang, action=action))

    apps = _load_state()
    entry = next((a for a in apps if a["slug"] == slug), None)
    if entry is None:
        raise DockerGateError(_t("dg_err_unknown_app", lang, slug=slug))

    compose_file = entry.get("compose_file")
    if not compose_file or not Path(compose_file).exists():
        raise DockerGateError(_t("dg_err_compose_file_not_found", lang))

    _run_docker_compose(entry["compose_project"], Path(compose_file), [action], _t("dg_err_action_failed", lang, action=action), lang=lang)


def get_container_logs(slug: str, tail: int = 200, lang: str = "en") -> str:
    apps = _load_state()
    entry = next((a for a in apps if a["slug"] == slug), None)
    if entry is None:
        raise DockerGateError(_t("dg_err_unknown_app", lang, slug=slug))

    container_name = entry.get("container_name")
    if not container_name:
        raise DockerGateError(_t("dg_err_no_container_for_app", lang))

    import docker as docker_lib
    client = _get_docker_client(lang)
    try:
        container = client.containers.get(container_name)
    except docker_lib.errors.NotFound:
        raise DockerGateError(_t("dg_err_container_not_found", lang, name=container_name))

    return container.logs(tail=tail, timestamps=True).decode("utf-8", errors="replace")


def get_container_stats(slug: str, lang: str = "en") -> dict:
    apps = _load_state()
    entry = next((a for a in apps if a["slug"] == slug), None)
    if entry is None:
        raise DockerGateError(_t("dg_err_unknown_app", lang, slug=slug))

    container_name = entry.get("container_name")
    if not container_name:
        raise DockerGateError(_t("dg_err_no_container_for_app", lang))

    import docker as docker_lib
    client = _get_docker_client(lang)
    try:
        container = client.containers.get(container_name)
    except docker_lib.errors.NotFound:
        raise DockerGateError(_t("dg_err_container_not_found", lang, name=container_name))

    if container.status != "running":
        return {"running": False}

    raw = container.stats(stream=False)

    cpu_stats = raw.get("cpu_stats", {})
    precpu_stats = raw.get("precpu_stats", {})
    cpu_usage = cpu_stats.get("cpu_usage", {}).get("total_usage")
    precpu_usage = precpu_stats.get("cpu_usage", {}).get("total_usage")
    system_usage = cpu_stats.get("system_cpu_usage")
    presystem_usage = precpu_stats.get("system_cpu_usage")
    online_cpus = cpu_stats.get("online_cpus") or 1

    cpu_percent = None
    if None not in (cpu_usage, precpu_usage, system_usage, presystem_usage):
        cpu_delta = cpu_usage - precpu_usage
        system_delta = system_usage - presystem_usage
        if system_delta > 0 and cpu_delta >= 0:
            cpu_percent = (cpu_delta / system_delta) * online_cpus * 100

    memory_stats = raw.get("memory_stats", {})
    mem_usage = memory_stats.get("usage")
    mem_limit = memory_stats.get("limit")

    networks = raw.get("networks") or {}
    rx_bytes = sum(iface.get("rx_bytes", 0) for iface in networks.values())
    tx_bytes = sum(iface.get("tx_bytes", 0) for iface in networks.values())

    return {
        "running": True,
        "cpu_percent": cpu_percent,
        "mem_usage": mem_usage,
        "mem_limit": mem_limit,
        "rx_bytes": rx_bytes,
        "tx_bytes": tx_bytes,
    }


def _known_volume_names(apps: list[dict]) -> set[str]:
    names = {a["volume_name"] for a in apps if a.get("volume_name")}
    names |= {c["volume_name"] for a in apps for c in a.get("companions", []) if c.get("volume_name")}
    return names


def _known_network_names(apps: list[dict]) -> set[str]:
    return {a["network_name"] for a in apps if a.get("network_name")}


def find_orphan_containers() -> list[dict]:
    known_names = _known_container_names(_load_state())
    client = _get_docker_client()
    orphans = []
    for c in client.containers.list(all=True):
        if c.name.startswith("docker-gate-") and c.name not in known_names:
            orphans.append({"name": c.name, "status": c.status, "image": c.image.tags})
    return orphans


def find_orphan_volumes() -> list[dict]:
    known_volumes = _known_volume_names(_load_state())
    client = _get_docker_client()
    orphans = []
    for v in client.volumes.list():
        if v.name.startswith("docker-gate-") and v.name.endswith("-data") and v.name not in known_volumes:
            orphans.append({"name": v.name})
    return orphans


def find_orphan_networks() -> list[dict]:
    known_networks = _known_network_names(_load_state())
    client = _get_docker_client()
    orphans = []
    for n in client.networks.list():
        if n.name.startswith("docker-gate-") and n.name.endswith("-net") and n.name not in known_networks:
            orphans.append({"name": n.name})
    return orphans


def find_dangling_images() -> list[dict]:
    client = _get_docker_client()
    images = client.images.list(filters={"dangling": True})
    return [{"id": img.short_id, "size_mb": round(img.attrs.get("Size", 0) / (1024 * 1024), 1)} for img in images]


def find_empty_domains(*, existing_domains_fn, domain_detail_fn) -> list[str]:
    domains = existing_domains_fn()
    known_apps_domains = {a["domain"] for a in _load_state()}
    empty = []
    for d in domains:
        try:
            info = domain_detail_fn(d)
        except Exception:
            continue
        apps_on_domain = info.get("apps", [])
        if not apps_on_domain and d not in known_apps_domains:
            empty.append(d)
    return empty


def remove_orphan_container(name: str, lang: str = "en") -> None:
    import docker as docker_lib
    if name in _known_container_names(_load_state()) or not name.startswith("docker-gate-"):
        raise DockerGateError(_t("dg_err_not_recognized_orphan_container", lang, name=name))
    client = _get_docker_client(lang)
    try:
        c = client.containers.get(name)
        c.stop()
        c.remove()
    except docker_lib.errors.NotFound:
        pass


def remove_orphan_volume(name: str, lang: str = "en") -> None:
    import docker as docker_lib
    if name in _known_volume_names(_load_state()) or not (name.startswith("docker-gate-") and name.endswith("-data")):
        raise DockerGateError(_t("dg_err_not_recognized_orphan_volume", lang, name=name))
    client = _get_docker_client(lang)
    try:
        client.volumes.get(name).remove()
    except docker_lib.errors.NotFound:
        pass


def remove_orphan_network(name: str, lang: str = "en") -> None:
    import docker as docker_lib
    if name in _known_network_names(_load_state()) or not (name.startswith("docker-gate-") and name.endswith("-net")):
        raise DockerGateError(_t("dg_err_not_recognized_orphan_network", lang, name=name))
    client = _get_docker_client(lang)
    try:
        client.networks.get(name).remove()
    except docker_lib.errors.NotFound:
        pass


def prune_dangling_images() -> int:
    client = _get_docker_client()
    result = client.images.prune(filters={"dangling": True})
    return result.get("SpaceReclaimed", 0)


def docker_ce_status() -> dict:
    installed = shutil.which("docker") is not None
    tracked, foreign = [], []
    if installed:
        known_names = _known_container_names(_load_state())
        try:
            client = _get_docker_client()
            for c in client.containers.list(all=True):
                (tracked if c.name in known_names else foreign).append(c.name)
        except DockerGateError:
            pass
    return {"installed": installed, "tracked_containers": tracked, "foreign_containers": foreign}


def _run_root_command(args: list[str], error_message: str, lang: str = "en") -> None:
    result = subprocess.run(["sudo", "-n"] + args, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise DockerGateError(_t("dg_err_with_detail", lang, message=error_message, detail=(result.stderr.strip() or result.stdout.strip())))


def uninstall_docker_ce(lang: str = "en") -> list[str]:
    commands = [
        (["systemctl", "stop", "docker", "docker.socket", "containerd"], _t("dg_err_docker_stop_failed", lang)),
        (
            [
                "apt-get", "purge", "-y",
                "docker-ce", "docker-ce-cli", "docker-ce-rootless-extras",
                "docker-buildx-plugin", "docker-compose-plugin", "containerd.io",
            ],
            _t("dg_err_purge_packages_failed", lang),
        ),
        (["apt-get", "autoremove", "-y"], _t("dg_err_autoremove_failed", lang)),
        (["rm", "-rf", "/var/lib/docker", "/var/lib/containerd", "/etc/docker"], _t("dg_err_remove_data_failed", lang)),
        (
            ["rm", "-f", "/etc/apt/sources.list.d/docker.list", "/etc/apt/keyrings/docker.gpg"],
            _t("dg_err_remove_apt_repo_failed", lang),
        ),
    ]
    warnings = []
    for args, error_message in commands:
        try:
            _run_root_command(args, error_message, lang=lang)
        except (DockerGateError, subprocess.TimeoutExpired) as e:
            warnings.append(str(e))

    try:
        _run_root_command(["groupdel", "docker"], _t("dg_err_remove_docker_group_failed", lang), lang=lang)
    except (DockerGateError, subprocess.TimeoutExpired):
        pass

    return warnings


_VOLUME_BACKUP_HELPER_IMAGE = "alpine:latest"


def backup_docker_volumes(dest_dir: Path) -> list[dict]:
    apps = _load_state()
    client = _get_docker_client()
    import docker as docker_lib

    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for volume_name in sorted(_known_volume_names(apps)):
        archive_name = f"{volume_name}.tar.gz"
        try:
            client.volumes.get(volume_name)
        except docker_lib.errors.NotFound:
            results.append({"volume": volume_name, "status": "missing", "archive": None})
            continue

        try:
            client.containers.run(
                _VOLUME_BACKUP_HELPER_IMAGE,
                command=["tar", "czf", f"/backup/{archive_name}", "-C", "/source", "."],
                volumes={
                    volume_name: {"bind": "/source", "mode": "ro"},
                    str(dest_dir): {"bind": "/backup", "mode": "rw"},
                },
                remove=True,
            )
        except docker_lib.errors.APIError as e:
            results.append({"volume": volume_name, "status": "error", "archive": None, "error": str(e)})
            continue

        archive_path = dest_dir / archive_name
        size = archive_path.stat().st_size if archive_path.exists() else 0
        results.append({"volume": volume_name, "status": "ok", "archive": str(archive_path), "size": size})

    return results


def restore_docker_volumes(src_dir: Path) -> list[dict]:
    apps = _load_state()
    known_volumes = _known_volume_names(apps)
    client = _get_docker_client()
    import docker as docker_lib

    src_dir = Path(src_dir)
    results = []
    if not src_dir.exists():
        return results

    for archive_path in sorted(src_dir.glob("*.tar.gz")):
        volume_name = archive_path.name[: -len(".tar.gz")]
        if volume_name not in known_volumes:
            results.append({"volume": volume_name, "status": "skipped_unknown", "archive": str(archive_path)})
            continue

        try:
            client.volumes.get(volume_name)
        except docker_lib.errors.NotFound:
            client.volumes.create(name=volume_name)

        try:
            client.containers.run(
                _VOLUME_BACKUP_HELPER_IMAGE,
                command=["tar", "xzf", f"/backup/{archive_path.name}", "-C", "/dest"],
                volumes={
                    volume_name: {"bind": "/dest", "mode": "rw"},
                    str(src_dir): {"bind": "/backup", "mode": "ro"},
                },
                remove=True,
            )
        except docker_lib.errors.APIError as e:
            results.append({"volume": volume_name, "status": "error", "archive": str(archive_path), "error": str(e)})
            continue

        results.append({"volume": volume_name, "status": "ok", "archive": str(archive_path)})

    return results


def restart_all_docker_apps(lang: str = "en") -> list[dict]:
    apps = _load_state()
    results = []
    for entry in apps:
        slug = entry.get("slug")
        compose_file = entry.get("compose_file")
        if not compose_file or not Path(compose_file).exists():
            results.append({"slug": slug, "status": "skipped_no_compose"})
            continue
        try:
            _run_docker_compose(
                entry["compose_project"], Path(compose_file),
                ["up", "-d", "--wait", "--wait-timeout", "120"],
                _t("dg_err_restart_app_failed", lang, slug=slug), lang=lang,
            )
            results.append({"slug": slug, "status": "started"})
        except DockerGateError as e:
            results.append({"slug": slug, "status": "error", "error": str(e)})
    return results


_LDAP_HOST = "host.docker.internal"
_LDAP_PORT = 1389
_LDAP_BASE_DN = "ou=users,dc=yunohost,dc=org"


def ldap_env_vars() -> dict:
    return {
        "LDAP_HOST": _LDAP_HOST,
        "LDAP_PORT": str(_LDAP_PORT),
        "LDAP_BASE_DN": _LDAP_BASE_DN,
    }


def _apply_ldap_wiring(service: dict, ldap_enabled: bool) -> None:
    if not ldap_enabled:
        service.pop("extra_hosts", None)
        return
    extra_hosts = [h for h in (service.get("extra_hosts") or []) if not h.startswith("host.docker.internal:")]
    extra_hosts.append("host.docker.internal:host-gateway")
    service["extra_hosts"] = extra_hosts


_LDAP_RELAY_SERVICE_NAME = "wappos-docker-ldap-relay.service"
_LDAP_RELAY_SCRIPT_PATH = Path(__file__).resolve().parent / "docker-ldap-relay.sh"
_LDAP_RELAY_UNIT_PATH = Path("/etc/systemd/system") / _LDAP_RELAY_SERVICE_NAME
_LDAP_RELAY_UNIT_TMP_PATH = Path("/tmp") / _LDAP_RELAY_SERVICE_NAME


def ensure_ldap_relay(lang: str = "en") -> None:
    status = subprocess.run(
        ["sudo", "-n", "systemctl", "is-active", _LDAP_RELAY_SERVICE_NAME],
        capture_output=True, text=True, timeout=10,
    )
    if status.stdout.strip() == "active":
        return

    if shutil.which("socat") is None:
        _run_root_command(["apt-get", "install", "-y", "socat"], _t("dg_err_install_socat_failed", lang), lang=lang)

    unit_content = (
        "[Unit]\n"
        f"Description={_t('dg_err_ldap_relay_description', lang)}\n"
        "After=docker.service slapd.service\n"
        "Requires=docker.service slapd.service\n\n"
        "[Service]\n"
        "Type=simple\n"
        f"ExecStart={_LDAP_RELAY_SCRIPT_PATH}\n"
        "Restart=on-failure\n"
        "RestartSec=5\n\n"
        "[Install]\n"
        "WantedBy=multi-user.target\n"
    )
    _LDAP_RELAY_UNIT_TMP_PATH.write_text(unit_content)
    try:
        _run_root_command(
            ["cp", str(_LDAP_RELAY_UNIT_TMP_PATH), str(_LDAP_RELAY_UNIT_PATH)],
            _t("dg_err_install_ldap_relay_failed", lang), lang=lang,
        )
    finally:
        _LDAP_RELAY_UNIT_TMP_PATH.unlink(missing_ok=True)
    _run_root_command(["systemctl", "daemon-reload"], _t("dg_err_systemd_reload_failed", lang), lang=lang)
    _run_root_command(
        ["systemctl", "enable", "--now", _LDAP_RELAY_SERVICE_NAME], _t("dg_err_ldap_relay_start_failed", lang), lang=lang,
    )


def _docker_hub_repository_ref(image: str) -> tuple[str, str] | None:
    without_digest = (image or "").split("@")[0]
    parts = without_digest.split("/")
    if len(parts) >= 2 and ("." in parts[0] or ":" in parts[0] or parts[0] == "localhost"):
        return None
    parts[-1] = parts[-1].split(":")[0]
    if len(parts) == 1:
        return "library", parts[0]
    if len(parts) == 2:
        return parts[0], parts[1]
    return None


def list_available_image_tags(image: str, limit: int = 25, lang: str = "en") -> list[dict]:
    ref = _docker_hub_repository_ref(image)
    if ref is None:
        raise DockerGateError(_t("dg_err_tag_list_unavailable", lang))
    namespace, repository = ref
    url = f"https://hub.docker.com/v2/repositories/{namespace}/{repository}/tags"
    try:
        resp = requests.get(url, params={"page_size": limit, "ordering": "last_updated"}, timeout=15)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise DockerGateError(_t("dg_err_docker_hub_query_failed", lang, detail=e))

    data = resp.json()
    return [
        {
            "name": t.get("name"),
            "last_updated": t.get("last_updated"),
            "digest": t.get("digest"),
        }
        for t in data.get("results", [])
        if t.get("name")
    ]


def check_docker_app_update(slug: str) -> dict:
    _, entry = _find_entry(slug)
    container_name = entry.get("container_name")
    image = entry.get("image")
    if not container_name or not image:
        return {"checked": False, "update_available": None}

    client = _get_docker_client()
    import docker as docker_lib
    try:
        container = client.containers.get(container_name)
        current_digest = container.image.id
    except docker_lib.errors.NotFound:
        return {"checked": False, "update_available": None}

    try:
        registry_data = client.images.get_registry_data(image)
        latest_digest = registry_data.id
    except docker_lib.errors.APIError as e:
        return {"checked": False, "update_available": None, "error": str(e)}

    return {
        "checked": True,
        "update_available": current_digest != latest_digest,
        "current_digest": current_digest,
        "latest_digest": latest_digest,
    }


def apply_docker_app_update(slug: str, target_tag: str | None = None, on_step=None, lang: str = "en") -> dict:
    with _state_lock():
        return _apply_docker_app_update_locked(slug, target_tag=target_tag, on_step=on_step, lang=lang)


def _apply_docker_app_update_locked(slug: str, target_tag: str | None = None, on_step=None, lang: str = "en") -> dict:
    def step(label):
        if on_step:
            on_step(label)

    step(_t("dg_step_check_parameters", lang))
    apps, entry = _find_entry(slug, lang=lang)
    compose_file = entry.get("compose_file")
    if not compose_file or not Path(compose_file).exists():
        raise DockerGateError(_t("dg_err_compose_file_not_found", lang))

    current_image = entry.get("image", "")
    if target_tag:
        base_image = current_image.split(":")[0].split("@")[0]
        new_image = f"{base_image}:{target_tag}"
    else:
        new_image = current_image

    compose_path = Path(compose_file)
    doc = yaml.safe_load(compose_path.read_text()) or {}
    main_key = _find_main_service_key(doc, entry.get("container_name"), lang=lang)
    doc["services"][main_key]["image"] = new_image

    step(_t("dg_step_write_configuration", lang))
    try:
        with open(compose_path, "w") as f:
            yaml.safe_dump(doc, f, sort_keys=False)
    except OSError as e:
        raise DockerGateError(_t("dg_err_write_config_failed", lang, detail=e))

    step(_t("dg_step_fetch_new_image", lang))
    _run_docker_compose(
        entry["compose_project"], compose_path, ["pull"], _t("dg_err_image_download_failed", lang),
        timeout=300, lang=lang,
    )

    step(_t("dg_step_restart_container", lang))
    _run_docker_compose(
        entry["compose_project"], compose_path,
        ["up", "-d", "--wait", "--wait-timeout", "120"],
        _t("dg_err_container_update_failed", lang), lang=lang,
    )

    entry["image"] = new_image
    entry["last_updated_at"] = int(time.time())
    _save_state(apps)
    return entry
