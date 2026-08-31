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

DATA_FILE = Path(__file__).parent / "data" / "docker_apps.json"
PORT_RANGE_START = 9100
PORT_RANGE_END = 9999

KNOWN_SPA_IMAGES = (
    "portainer", "dashy", "heimdall", "homepage", "homarr", "organizr", "flame",
)


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


def _get_docker_client():
    global _docker_client, _docker_client_error
    if _docker_client is not None:
        return _docker_client
    try:
        import docker
        _docker_client = docker.from_env()
        return _docker_client
    except Exception as e:
        _docker_client_error = str(e)
        raise DockerGateError(
            f"Impossible de contacter le démon Docker — vérifiez qu'il est installé et démarré ({e})."
        )


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


def _validate_cpu_limit(cpu_limit: str) -> str | None:
    cpu_limit = (cpu_limit or "").strip()
    if not cpu_limit:
        return None
    if not re.fullmatch(r"\d+(\.\d+)?", cpu_limit) or float(cpu_limit) <= 0:
        raise DockerGateError(f"Limite CPU invalide : « {cpu_limit} » (attendu un nombre positif, ex. 0.5).")
    return cpu_limit


def _validate_mem_limit(mem_limit: str) -> str | None:
    mem_limit = (mem_limit or "").strip()
    if not mem_limit:
        return None
    if not re.fullmatch(r"\d+[mMgG]", mem_limit):
        raise DockerGateError(
            f"Limite mémoire invalide : « {mem_limit} » — attendu un nombre suivi de m (méga-octets) ou g (giga-octets), ex. 512m ou 1g."
        )
    return mem_limit


def _pick_free_port() -> int:
    used = {a["host_port"] for a in _load_state()}

    client = _get_docker_client()
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

    raise DockerGateError("Aucun port libre disponible dans la plage 9100-9999.")


def build_create_steps(mode: str) -> list[str]:
    steps = ["Vérification des paramètres", "Sélection du port"]
    if mode == "subdomain":
        steps += [
            "Création du domaine",
            "Diagnostic DNS",
            "Diagnostic Web",
            "Obtention du certificat",
            "Vérification du certificat",
        ]
    steps += ["Écriture de la configuration", "Démarrage du conteneur", "Exposition de l'app"]
    return steps


def build_edit_steps() -> list[str]:
    return ["Vérification des paramètres", "Écriture de la configuration", "Redémarrage du conteneur"]


def fetch_compose_from_url(url: str) -> str:
    if not url.startswith("https://"):
        raise DockerGateError("Seules les URL https:// sont acceptées.")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        raise DockerGateError(f"Impossible de récupérer l'URL ({e}).")
    if len(response.content) > 200_000:
        raise DockerGateError("Fichier trop volumineux (>200 Ko).")
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


def inspect_docker_image(image_name: str) -> dict:
    client = _get_docker_client()
    import docker as docker_lib
    try:
        image = client.images.pull(image_name)
    except docker_lib.errors.APIError as e:
        raise DockerGateError(f"Impossible de télécharger l'image « {image_name} » ({e}).")

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


def parse_docker_run_command(text: str) -> dict:
    joined = re.sub(r"\\\s*\n", " ", text)
    joined = joined.replace("\n", " ").strip()
    if not joined.startswith("docker "):
        raise DockerGateError("Ce texte ne ressemble pas à une commande « docker run ».")

    try:
        tokens = shlex.split(joined)
    except ValueError as e:
        raise DockerGateError(f"Impossible d'analyser la commande ({e}).")

    if "run" not in tokens:
        raise DockerGateError("Aucun sous-commande « run » trouvée.")

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
                warnings.append("Plusieurs ports publiés — seul le premier a été retenu.")
            i += 2
            continue
        if tok in ("-v", "--volume") and i + 1 < len(tokens):
            parts = tokens[i + 1].split(":")
            if len(parts) >= 2:
                if result["data_path"] is None:
                    result["data_path"] = parts[1]
                else:
                    warnings.append("Plusieurs volumes montés — seul le premier a été retenu.")
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
        raise DockerGateError("Aucune image Docker trouvée dans cette commande.")

    result["warnings"] = warnings
    return result


def smart_parse_input(text: str, env_example_text=None) -> dict:
    stripped = text.strip()
    if not stripped:
        raise DockerGateError("Rien à analyser.")

    if stripped.startswith("docker "):
        result = parse_docker_run_command(stripped)
    elif "\n" in stripped or stripped.lstrip().startswith(("services:", "image:")):
        result = parse_compose_snippet(stripped, env_example_text=env_example_text)
    elif re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._/-]*(:[a-zA-Z0-9._-]+)?", stripped):
        result = inspect_docker_image(stripped)
    else:
        raise DockerGateError("Format non reconnu — collez une image, une commande « docker run » ou un docker-compose.yml.")

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


def _extract_compose_service_fields(service, service_key, sibling_service_keys=None, env_example_vars=None):
    result = {"image": None, "container_port": None, "data_path": None, "env_vars": None, "url_env_var": None,
              "service_key": service_key,
              "suggested_slug": service.get("container_name") or service_key}
    warnings = []
    pairs = []

    if service.get("env_file"):
        if env_example_vars:
            pairs.extend(env_example_vars.items())
        else:
            warnings.append("« env_file » n'est pas supporté — ajoutez les variables manuellement.")

    if "image" in service:
        result["image"] = str(service["image"])

    ports = service.get("ports")
    if ports and isinstance(ports, list) and ports:
        first = str(ports[0])
        result["container_port"] = _strip_port_protocol(first.split(":")[-1])
        if len(ports) > 1:
            warnings.append("Plusieurs ports déclarés — seul le premier a été retenu.")

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
            warnings.append("Plusieurs volumes déclarés — seul le premier a été retenu.")

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


def parse_compose_snippet(text: str, env_example_text=None) -> dict:
    env_example_vars = None
    if env_example_text:
        try:
            env_example_vars = parse_env_vars_text(env_example_text)
        except DockerGateError:
            pass

    text, unresolved_vars = _substitute_compose_vars(text, defaults=env_example_vars)

    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as e:
        raise DockerGateError(f"docker-compose.yml invalide ({e}).")

    if not isinstance(data, dict):
        raise DockerGateError("Ce contenu ne ressemble pas à un docker-compose.yml valide.")

    if "services" in data and isinstance(data["services"], dict):
        services = data["services"]
        if not services:
            raise DockerGateError("Aucun service trouvé dans ce docker-compose.yml.")
    else:
        services = {None: data}

    compose_warnings = []
    if unresolved_vars:
        compose_warnings.append(f"Variables non résolues : {', '.join(sorted(set(unresolved_vars)))}.")

    if len(services) > 1:
        all_service_keys = set(services.keys())
        parsed_services = []
        env_example_applied = False
        for service_key, service in services.items():
            if not isinstance(service, dict):
                raise DockerGateError("Format de service non reconnu.")
            sibling_keys = all_service_keys - {service_key}
            if env_example_vars and service.get("env_file"):
                env_example_applied = True
            service_result, service_warnings = _extract_compose_service_fields(
                service, service_key, sibling_keys, env_example_vars=env_example_vars)
            service_result["warnings"] = service_warnings
            parsed_services.append(service_result)
        if not any(s["image"] for s in parsed_services):
            raise DockerGateError("Aucune image trouvée dans ce docker-compose.yml.")
        if env_example_applied:
            compose_warnings.append("Fichier d'exemple d'environnement du projet utilisé pour compléter env_file.")
        generated = _autogenerate_secrets(parsed_services)
        if generated:
            compose_warnings.append(f"Secrets auto-générés : {', '.join(generated)}.")
        return {"multi_service": True, "services": parsed_services, "warnings": compose_warnings}

    service_key, service = next(iter(services.items()))
    if not isinstance(service, dict):
        raise DockerGateError("Format de service non reconnu.")

    result, service_warnings = _extract_compose_service_fields(service, service_key, env_example_vars=env_example_vars)
    if env_example_vars and service.get("env_file"):
        compose_warnings.append("Fichier d'exemple d'environnement du projet utilisé pour compléter env_file.")

    if not result["image"] and not result["container_port"] and not result["data_path"] and not result["env_vars"]:
        raise DockerGateError("Rien d'exploitable n'a été trouvé dans ce docker-compose.yml.")

    result["warnings"] = compose_warnings + service_warnings
    return result


def parse_env_vars_text(text: str) -> dict:
    env = {}
    for i, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise DockerGateError(f"Ligne {i} invalide (pas de « = ») : {line}")
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip()
    return env


def _compose_dir(slug: str) -> Path:
    return Path(__file__).parent / "data" / "compose" / slug


_CONFIG_FILE_NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")


def _write_bind_mount_file(slug: str, relative_name: str, content: str) -> None:
    if not _CONFIG_FILE_NAME_RE.fullmatch(relative_name or ""):
        raise DockerGateError(f"Nom de fichier de configuration invalide : « {relative_name} ».")
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


def _run_docker_compose(project_name, compose_path, args, error_message, timeout=180):
    try:
        result = subprocess.run(
            ["docker", "compose", "-p", project_name, "-f", str(compose_path)] + args,
            capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise DockerGateError(f"{error_message} (délai dépassé après {timeout}s).")
    if result.returncode != 0:
        raise DockerGateError(f"{error_message} : {result.stderr.strip() or result.stdout.strip()}")
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


def resolve_target_url(mode, domain, domain_parent, path, new_subdomain):
    if mode == "subdomain":
        if not new_subdomain or not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,62}", new_subdomain):
            raise DockerGateError("Sous-domaine invalide.")
        if not domain_parent:
            raise DockerGateError("Domaine parent manquant.")
        return f"https://{new_subdomain}.{domain_parent}/"

    if not domain:
        raise DockerGateError("Domaine manquant.")
    normalized_path = path if path.startswith("/") else f"/{path}"
    if not re.fullmatch(r"/[a-zA-Z0-9._~-]*(?:/[a-zA-Z0-9._~-]+)*", normalized_path):
        raise DockerGateError("Chemin invalide.")
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
    ldap_enabled=False, logo_bytes=None, on_step=None,
    *,
    add_domain_fn, run_diagnosis_fn, install_cert_fn, domain_detail_fn,
    install_app_fn, list_app_ids_fn, set_permission_logo_fn=None,
):
    warnings = []

    def step(label):
        if on_step:
            on_step(label)

    step("Vérification des paramètres")
    if not _slug_is_valid(slug):
        raise DockerGateError("Identifiant (slug) invalide — lettres minuscules, chiffres et tirets uniquement.")
    if _slug_already_used(slug):
        raise DockerGateError(f"L'identifiant « {slug} » est déjà utilisé.")

    try:
        container_port = int(container_port)
    except (TypeError, ValueError):
        raise DockerGateError("Le port du conteneur doit être un nombre.")

    cpu_limit = _validate_cpu_limit(cpu_limit)
    mem_limit = _validate_mem_limit(mem_limit)

    if mode == "subdomain":
        if not new_subdomain or not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,62}", new_subdomain):
            raise DockerGateError("Sous-domaine invalide.")
        if not domain_parent:
            raise DockerGateError("Domaine parent manquant.")
        target_domain = f"{new_subdomain}.{domain_parent}"
        target_path = "/"
    else:
        if not domain:
            raise DockerGateError("Domaine manquant.")
        normalized_path = path if path.startswith("/") else f"/{path}"
        if not re.fullmatch(r"/[a-zA-Z0-9._~-]*(?:/[a-zA-Z0-9._~-]+)*", normalized_path):
            raise DockerGateError("Chemin invalide.")
        target_domain = domain
        target_path = normalized_path

    permission_group = visibility if visibility in ("admins", "all_users", "visitors") else "admins"

    with _state_lock():
        step("Sélection du port")
        host_port = _pick_free_port()

        if mode == "subdomain":
            if not reuse_existing_domain:
                step("Création du domaine")
                add_domain_fn(target_domain)

            step("Diagnostic DNS")
            if not run_diagnosis_fn("dnsrecords"):
                warnings.append(f"Le diagnostic DNS de {target_domain} n'a pas pu être vérifié.")

            step("Diagnostic Web")
            if not run_diagnosis_fn("web"):
                warnings.append(f"Le diagnostic Web de {target_domain} n'a pas pu être vérifié.")

            step("Obtention du certificat")
            try:
                install_cert_fn(target_domain)
            except Exception:
                pass

            step("Vérification du certificat")
            ca_type = None
            try:
                detail = domain_detail_fn(target_domain)
                ca_type = (detail.get("certificate") or {}).get("CA_type")
            except Exception as e:
                warnings.append(f"Impossible de vérifier le certificat de {target_domain} ({e}).")

            if ca_type and ca_type != "letsencrypt":
                warnings.append(
                    f"Le certificat de {target_domain} n'est pas Let's Encrypt (« {ca_type} »). "
                    "Vérifiez la configuration DNS et le transfert TLS, puis relancez l'installation."
                )

        if url_env_var:
            env_vars = dict(env_vars) if env_vars else {}
            if target_path == "/":
                env_vars[url_env_var] = f"https://{target_domain}/"
            else:
                env_vars[url_env_var] = f"https://{target_domain}{target_path}"

        main_key = main_service_key or "app"
        project_name = f"docker-gate-{slug}"
        compose_path = _compose_dir(slug) / "docker-compose.yml"

        step("Écriture de la configuration")
        if ldap_enabled:
            ensure_ldap_relay()
        resolved_config_files = []
        for cf in config_files or []:
            container_path = (cf.get("container_path") or "").strip()
            filename = (cf.get("filename") or "").strip()
            if not container_path.startswith("/"):
                raise DockerGateError(f"Chemin de fichier de configuration invalide : « {container_path} ».")
            _write_bind_mount_file(slug, filename, cf.get("content") or "")
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
            raise DockerGateError(f"Impossible d'écrire la configuration ({e}).")

        step("Démarrage du conteneur")
        _run_docker_compose(project_name, compose_path, ["config", "-q"], "Configuration invalide", timeout=30)
        try:
            _run_docker_compose(
                project_name, compose_path,
                ["up", "-d", "--wait", "--wait-timeout", "120", "--pull", "missing"],
                "Échec du démarrage du conteneur", timeout=240,
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

    step("Exposition de l'app")
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
            warnings.append(f"Le logo de l'app n'a pas pu être appliqué ({e}).")

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


def _find_entry(slug: str) -> tuple[list[dict], dict]:
    apps = _load_state()
    entry = next((a for a in apps if a["slug"] == slug), None)
    if entry is None:
        raise DockerGateError(f"App inconnue : {slug}")
    return apps, entry


def get_app_entry(slug: str) -> dict:
    _, entry = _find_entry(slug)
    return entry


def get_app_entry_by_yunohost_id(yunohost_app_id: str) -> dict | None:
    apps = _load_state()
    return next((a for a in apps if a.get("yunohost_app_id") == yunohost_app_id), None)


def get_all_yunohost_app_ids() -> set[str]:
    apps = _load_state()
    return {a["yunohost_app_id"] for a in apps if a.get("yunohost_app_id")}


def _find_main_service_key(doc: dict, container_name: str) -> str:
    services = doc.get("services", {})
    for key, service in services.items():
        if service.get("container_name") == container_name:
            return key
    if services:
        return next(iter(services))
    raise DockerGateError("Aucun service trouvé dans la configuration du conteneur.")


def read_current_env_vars(slug: str) -> dict:
    _, entry = _find_entry(slug)
    compose_file = entry.get("compose_file")
    if not compose_file or not Path(compose_file).exists():
        return {}
    doc = yaml.safe_load(Path(compose_file).read_text()) or {}
    main_key = _find_main_service_key(doc, entry.get("container_name"))
    return doc.get("services", {}).get(main_key, {}).get("environment") or {}


def update_docker_app(slug, image, container_port, data_path="", env_vars=None, cpu_limit="", mem_limit="",
                       ldap_enabled=None, on_step=None):
    with _state_lock():
        return _update_docker_app_locked(
            slug, image, container_port, data_path=data_path, env_vars=env_vars, cpu_limit=cpu_limit,
            mem_limit=mem_limit, ldap_enabled=ldap_enabled, on_step=on_step,
        )


def _update_docker_app_locked(slug, image, container_port, data_path="", env_vars=None, cpu_limit="", mem_limit="",
                               ldap_enabled=None, on_step=None):
    warnings = []

    def step(label):
        if on_step:
            on_step(label)

    step("Vérification des paramètres")
    apps, entry = _find_entry(slug)

    compose_file = entry.get("compose_file")
    if not compose_file or not Path(compose_file).exists():
        raise DockerGateError(
            "Fichier compose introuvable pour cette app — elle a peut-être été créée avant cette fonctionnalité."
        )

    image = (image or "").strip()
    if not image:
        raise DockerGateError("L'image Docker est obligatoire.")
    try:
        container_port = int(container_port)
    except (TypeError, ValueError):
        raise DockerGateError("Le port du conteneur doit être un nombre.")
    cpu_limit = _validate_cpu_limit(cpu_limit)
    mem_limit = _validate_mem_limit(mem_limit)
    data_path = (data_path or "").strip()

    compose_path = Path(compose_file)
    doc = yaml.safe_load(compose_path.read_text()) or {}
    main_key = _find_main_service_key(doc, entry.get("container_name"))
    main_service = doc["services"][main_key]

    step("Écriture de la configuration")
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
        raise DockerGateError(f"Impossible d'écrire la configuration ({e}).")

    if effective_ldap_enabled:
        ensure_ldap_relay()

    step("Redémarrage du conteneur")
    _run_docker_compose(entry["compose_project"], compose_path, ["config", "-q"], "Configuration invalide", timeout=30)
    _run_docker_compose(
        entry["compose_project"], compose_path,
        ["up", "-d", "--wait", "--wait-timeout", "120"],
        "Échec de la mise à jour du conteneur", timeout=180,
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


def remove_docker_app(slug, delete_data=False, delete_domain=False, *, remove_app_fn, remove_domain_fn=None):
    with _state_lock():
        return _remove_docker_app_locked(
            slug, delete_data=delete_data, delete_domain=delete_domain,
            remove_app_fn=remove_app_fn, remove_domain_fn=remove_domain_fn,
        )


def _remove_docker_app_locked(slug, delete_data=False, delete_domain=False, *, remove_app_fn, remove_domain_fn=None):
    apps = _load_state()
    entry = next((a for a in apps if a["slug"] == slug), None)
    if entry is None:
        raise DockerGateError(f"App inconnue : {slug}")

    warnings = []

    if entry.get("yunohost_app_id"):
        try:
            remove_app_fn(entry["yunohost_app_id"])
        except Exception as e:
            warnings.append(f"Échec du retrait de l'exposition YunoHost : {e}")
        _remove_stale_app_logo(entry["yunohost_app_id"])

    if entry.get("compose_project"):
        compose_file = Path(entry["compose_file"]) if entry.get("compose_file") else None
        down_args = ["down", "-v", "--rmi", "all"] if delete_data else ["down"]
        try:
            if compose_file and compose_file.exists():
                _run_docker_compose(entry["compose_project"], compose_file, down_args, "Échec de l'arrêt du conteneur")
            else:
                result = subprocess.run(
                    ["docker", "compose", "-p", entry["compose_project"]] + down_args,
                    capture_output=True, text=True, timeout=180,
                )
                if result.returncode != 0:
                    raise DockerGateError(f"Échec de l'arrêt du conteneur : {result.stderr.strip()}")
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
            warnings.append(f"Échec de la suppression du domaine : {e}")

    apps = [a for a in apps if a["slug"] != slug]
    _save_state(apps)

    return warnings


_CONTAINER_ACTIONS = ("start", "stop", "restart")


def container_action(slug: str, action: str) -> None:
    if action not in _CONTAINER_ACTIONS:
        raise DockerGateError(f"Action inconnue : {action}")

    apps = _load_state()
    entry = next((a for a in apps if a["slug"] == slug), None)
    if entry is None:
        raise DockerGateError(f"App inconnue : {slug}")

    compose_file = entry.get("compose_file")
    if not compose_file or not Path(compose_file).exists():
        raise DockerGateError(
            "Fichier compose introuvable pour cette app — elle a peut-être été créée avant cette fonctionnalité."
        )

    _run_docker_compose(entry["compose_project"], Path(compose_file), [action], f"Échec du {action}")


def get_container_logs(slug: str, tail: int = 200) -> str:
    apps = _load_state()
    entry = next((a for a in apps if a["slug"] == slug), None)
    if entry is None:
        raise DockerGateError(f"App inconnue : {slug}")

    container_name = entry.get("container_name")
    if not container_name:
        raise DockerGateError("Aucun conteneur associé à cette app.")

    import docker as docker_lib
    client = _get_docker_client()
    try:
        container = client.containers.get(container_name)
    except docker_lib.errors.NotFound:
        raise DockerGateError(f"Conteneur « {container_name} » introuvable.")

    return container.logs(tail=tail, timestamps=True).decode("utf-8", errors="replace")


def get_container_stats(slug: str) -> dict:
    apps = _load_state()
    entry = next((a for a in apps if a["slug"] == slug), None)
    if entry is None:
        raise DockerGateError(f"App inconnue : {slug}")

    container_name = entry.get("container_name")
    if not container_name:
        raise DockerGateError("Aucun conteneur associé à cette app.")

    import docker as docker_lib
    client = _get_docker_client()
    try:
        container = client.containers.get(container_name)
    except docker_lib.errors.NotFound:
        raise DockerGateError(f"Conteneur « {container_name} » introuvable.")

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


def remove_orphan_container(name: str) -> None:
    import docker as docker_lib
    if name in _known_container_names(_load_state()) or not name.startswith("docker-gate-"):
        raise DockerGateError(f"« {name} » n'est pas un conteneur orphelin reconnu.")
    client = _get_docker_client()
    try:
        c = client.containers.get(name)
        c.stop()
        c.remove()
    except docker_lib.errors.NotFound:
        pass


def remove_orphan_volume(name: str) -> None:
    import docker as docker_lib
    if name in _known_volume_names(_load_state()) or not (name.startswith("docker-gate-") and name.endswith("-data")):
        raise DockerGateError(f"« {name} » n'est pas un volume orphelin reconnu.")
    client = _get_docker_client()
    try:
        client.volumes.get(name).remove()
    except docker_lib.errors.NotFound:
        pass


def remove_orphan_network(name: str) -> None:
    import docker as docker_lib
    if name in _known_network_names(_load_state()) or not (name.startswith("docker-gate-") and name.endswith("-net")):
        raise DockerGateError(f"« {name} » n'est pas un réseau orphelin reconnu.")
    client = _get_docker_client()
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


def _run_root_command(args: list[str], error_message: str) -> None:
    result = subprocess.run(["sudo", "-n"] + args, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise DockerGateError(f"{error_message} : {result.stderr.strip() or result.stdout.strip()}")


def uninstall_docker_ce() -> list[str]:
    commands = [
        (["systemctl", "stop", "docker", "docker.socket", "containerd"], "Échec de l'arrêt de Docker"),
        (
            [
                "apt-get", "purge", "-y",
                "docker-ce", "docker-ce-cli", "docker-ce-rootless-extras",
                "docker-buildx-plugin", "docker-compose-plugin", "containerd.io",
            ],
            "Échec de la purge des paquets Docker",
        ),
        (["apt-get", "autoremove", "-y"], "Échec du nettoyage des paquets orphelins"),
        (["rm", "-rf", "/var/lib/docker", "/var/lib/containerd", "/etc/docker"], "Échec de la suppression des données Docker"),
        (
            ["rm", "-f", "/etc/apt/sources.list.d/docker.list", "/etc/apt/keyrings/docker.gpg"],
            "Échec de la suppression du dépôt APT Docker",
        ),
    ]
    warnings = []
    for args, error_message in commands:
        try:
            _run_root_command(args, error_message)
        except (DockerGateError, subprocess.TimeoutExpired) as e:
            warnings.append(str(e))

    try:
        _run_root_command(["groupdel", "docker"], "Échec de la suppression du groupe docker")
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


def restart_all_docker_apps() -> list[dict]:
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
                f"Échec du redémarrage de {slug}",
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


def ensure_ldap_relay() -> None:
    status = subprocess.run(
        ["sudo", "-n", "systemctl", "is-active", _LDAP_RELAY_SERVICE_NAME],
        capture_output=True, text=True, timeout=10,
    )
    if status.stdout.strip() == "active":
        return

    if shutil.which("socat") is None:
        _run_root_command(["apt-get", "install", "-y", "socat"], "Impossible d'installer socat")

    unit_content = (
        "[Unit]\n"
        "Description=Relais TCP LDAP pour les conteneurs Docker Gate\n"
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
            "Impossible d'installer le service de relais LDAP",
        )
    finally:
        _LDAP_RELAY_UNIT_TMP_PATH.unlink(missing_ok=True)
    _run_root_command(["systemctl", "daemon-reload"], "Échec du rechargement systemd")
    _run_root_command(
        ["systemctl", "enable", "--now", _LDAP_RELAY_SERVICE_NAME], "Échec du démarrage du relais LDAP"
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


def list_available_image_tags(image: str, limit: int = 25) -> list[dict]:
    ref = _docker_hub_repository_ref(image)
    if ref is None:
        raise DockerGateError(
            "Liste des versions non disponible pour ce registre — seul Docker Hub est supporté pour l'instant."
        )
    namespace, repository = ref
    url = f"https://hub.docker.com/v2/repositories/{namespace}/{repository}/tags"
    try:
        resp = requests.get(url, params={"page_size": limit, "ordering": "last_updated"}, timeout=15)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise DockerGateError(f"Impossible d'interroger Docker Hub ({e}).")

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


def apply_docker_app_update(slug: str, target_tag: str | None = None, on_step=None) -> dict:
    with _state_lock():
        return _apply_docker_app_update_locked(slug, target_tag=target_tag, on_step=on_step)


def _apply_docker_app_update_locked(slug: str, target_tag: str | None = None, on_step=None) -> dict:
    def step(label):
        if on_step:
            on_step(label)

    step("Vérification des paramètres")
    apps, entry = _find_entry(slug)
    compose_file = entry.get("compose_file")
    if not compose_file or not Path(compose_file).exists():
        raise DockerGateError(
            "Fichier compose introuvable pour cette app — elle a peut-être été créée avant cette fonctionnalité."
        )

    current_image = entry.get("image", "")
    if target_tag:
        base_image = current_image.split(":")[0].split("@")[0]
        new_image = f"{base_image}:{target_tag}"
    else:
        new_image = current_image

    compose_path = Path(compose_file)
    doc = yaml.safe_load(compose_path.read_text()) or {}
    main_key = _find_main_service_key(doc, entry.get("container_name"))
    doc["services"][main_key]["image"] = new_image

    step("Écriture de la configuration")
    try:
        with open(compose_path, "w") as f:
            yaml.safe_dump(doc, f, sort_keys=False)
    except OSError as e:
        raise DockerGateError(f"Impossible d'écrire la configuration ({e}).")

    step("Récupération de la nouvelle image")
    _run_docker_compose(
        entry["compose_project"], compose_path, ["pull"], "Échec du téléchargement de la nouvelle image",
        timeout=300,
    )

    step("Redémarrage du conteneur")
    _run_docker_compose(
        entry["compose_project"], compose_path,
        ["up", "-d", "--wait", "--wait-timeout", "120"],
        "Échec de la mise à jour du conteneur",
    )

    entry["image"] = new_image
    entry["last_updated_at"] = int(time.time())
    _save_state(apps)
    return entry
