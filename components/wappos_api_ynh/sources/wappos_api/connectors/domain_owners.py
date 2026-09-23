# Auteur : Patrick Ritaine

from __future__ import annotations

import fcntl
import json
import threading
from pathlib import Path

from wappos_api.config import settings
from wappos_api.errors import UpstreamValidationError

_lock = threading.Lock()


def _registry_path() -> Path:
    return Path(settings.wappos_domain_owners_path)


def _load() -> dict[str, list[str]]:
    path = _registry_path()
    if not path.exists():
        return {}
    with open(path, "rb") as f:
        fcntl.flock(f, fcntl.LOCK_SH)
        try:
            raw = f.read()
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)
    if not raw.strip():
        return {}
    return json.loads(raw)


def _save(registry: dict[str, list[str]]) -> None:
    path = _registry_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a+b") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            f.seek(0)
            f.truncate()
            f.write(json.dumps(registry, indent=2, sort_keys=True).encode())
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def list_owners() -> dict[str, list[str]]:
    with _lock:
        return _load()


def get_owners(domain: str) -> list[str]:
    with _lock:
        return list(_load().get(domain, []))


def set_owners(domain: str, owners: list[str]) -> None:
    deduped = sorted(set(owners))
    with _lock:
        registry = _load()
        previous = set(registry.get(domain, []))
        if deduped:
            registry[domain] = deduped
        else:
            registry.pop(domain, None)
        _save(registry)
    for removed_user in previous - set(deduped):
        clear_primary_domain_if_matches(removed_user, domain)


def add_owner(domain: str, username: str) -> list[str]:
    with _lock:
        registry = _load()
        owners = set(registry.get(domain, []))
        owners.add(username)
        registry[domain] = sorted(owners)
        _save(registry)
        return registry[domain]


def remove_owner(domain: str, username: str) -> list[str]:
    with _lock:
        registry = _load()
        owners = set(registry.get(domain, []))
        owners.discard(username)
        if owners:
            registry[domain] = sorted(owners)
        else:
            registry.pop(domain, None)
        _save(registry)
        result = registry.get(domain, [])
    clear_primary_domain_if_matches(username, domain)
    return result


def find_parent_domain(new_domain: str) -> str | None:
    with _lock:
        registry = _load()
    candidates = [
        registered
        for registered in registry
        if registered != new_domain and new_domain.endswith("." + registered)
    ]
    if not candidates:
        return None
    return max(candidates, key=len)


def inherit_ownership_for_new_domain(new_domain: str) -> list[str]:
    parent = find_parent_domain(new_domain)
    if parent is None:
        return []
    with _lock:
        registry = _load()
        inherited = list(registry.get(parent, []))
        if inherited:
            registry[new_domain] = inherited
            _save(registry)
        return inherited


def domains_owned_by(username: str) -> list[str]:
    return sorted(domain for domain, owners in list_owners().items() if username in owners)


def _primary_registry_path() -> Path:
    return Path(settings.wappos_domain_admin_primary_path)


def _load_primary() -> dict[str, str]:
    path = _primary_registry_path()
    if not path.exists():
        return {}
    with open(path, "rb") as f:
        fcntl.flock(f, fcntl.LOCK_SH)
        try:
            raw = f.read()
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)
    if not raw.strip():
        return {}
    return json.loads(raw)


def _save_primary(registry: dict[str, str]) -> None:
    path = _primary_registry_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a+b") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            f.seek(0)
            f.truncate()
            f.write(json.dumps(registry, indent=2, sort_keys=True).encode())
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def get_primary_domain(username: str) -> str | None:
    with _lock:
        return _load_primary().get(username)


def set_primary_domain(username: str, domain: str) -> None:
    if domain not in domains_owned_by(username):
        raise UpstreamValidationError(
            f"Domain {domain} is not owned by {username}", error_key="primary_domain_not_owned", detail=domain
        )
    with _lock:
        registry = _load_primary()
        registry[username] = domain
        _save_primary(registry)


def clear_primary_domain_if_matches(username: str, domain: str) -> None:
    with _lock:
        registry = _load_primary()
        if registry.get(username) == domain:
            registry.pop(username)
            _save_primary(registry)


def require_known_domain_format(domain: str) -> None:
    if not domain or "/" in domain or ".." in domain:
        raise UpstreamValidationError(
            f"Invalid domain name: {domain}", error_key="invalid_domain", detail=domain
        )
