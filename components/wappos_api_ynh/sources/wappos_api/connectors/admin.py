# Auteur : Patrick Ritaine

from __future__ import annotations

import fcntl
import functools
import http.cookies
import json
import logging
import os
import pickle
import socket
import subprocess
import threading
import time
import tomllib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

from wappos_api.config import settings
from wappos_api.errors import (
    InvalidCredentialsError,
    UpstreamProtocolError,
    UpstreamUnavailableError,
    UpstreamValidationError,
)
from wappos_api.schemas.app import (
    AppCatalog,
    AppCatalogAntifeature,
    AppCatalogCategory,
    AppCatalogEntry,
    AppCatalogSubtag,
    AppDetail,
    AppInfo,
    AppManifest,
    AppUpgradeInfo,
    AppUpstreamInfo,
)
from wappos_api.schemas.diagnosis import DiagnosisItem, DiagnosisReport
from wappos_api.schemas.domain import DomainApp, DomainCertificate, DomainDetail
from wappos_api.schemas.firewall import FirewallPort, FirewallRules
from wappos_api.schemas.group import GroupInfo
from wappos_api.schemas.log import LogDetail, LogEntry, LogSuboperation
from wappos_api.schemas.permission import PermissionInfo
from wappos_api.schemas.service import ServiceInfo
from wappos_api.schemas.storage import (
    DiskInfo,
    MountConsumer,
    MountInfo,
    SmartAttribute,
    SmartReport,
)
from wappos_api.schemas.system import SystemHealth, WapposComponentVersion
from wappos_api.schemas.user import User, UserDetail

_SPECIAL_GROUPS = {"visitors", "all_users", "admins"}

logger = logging.getLogger("wappos_api")

_YUNOHOST_API_HEADERS = {"X-Requested-With": "customscript", "locale": "fr"}

_SESSION_COOKIE_NAME = "yunohost.admin"


_TTL_CACHE_DIR = Path("/dev/shm/wappos_api_cache")


def _ttl_cache_load(cache_file: Path) -> dict:
    if not cache_file.exists():
        return {}
    try:
        with open(cache_file, "rb") as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            try:
                return pickle.load(f)
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
    except (EOFError, pickle.UnpicklingError, OSError):
        return {}


def _ttl_cache(ttl_seconds: float):
    def decorator(func):
        lock = threading.Lock()

        def _cache_file() -> Path:
            return _TTL_CACHE_DIR / f"{func.__name__}.cache"

        @functools.wraps(func)
        def wrapper(session_token: str, *args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            now = time.time()
            cache_file = _cache_file()
            with lock:
                store = _ttl_cache_load(cache_file)
                cached = store.get(key)
                if cached and now - cached[0] < ttl_seconds:
                    return cached[1]

            result = func(session_token, *args, **kwargs)

            with lock:
                _TTL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
                with open(cache_file, "a+b") as f:
                    fcntl.flock(f, fcntl.LOCK_EX)
                    try:
                        f.seek(0)
                        try:
                            store = pickle.load(f)
                        except (EOFError, pickle.UnpicklingError):
                            store = {}
                        store[key] = (now, result)
                        f.seek(0)
                        f.truncate()
                        pickle.dump(store, f)
                    finally:
                        fcntl.flock(f, fcntl.LOCK_UN)
            return result

        def cache_clear() -> None:
            with lock:
                _cache_file().unlink(missing_ok=True)

        wrapper.cache_clear = cache_clear
        return wrapper

    return decorator

_NATIVE_SERVICE_LOCK_FILES = {
    settings.yunohost_api_base_url: Path(__file__).parent.parent.parent / ".package" / "yunohost_api.lock",
    settings.portalapi_base_url: Path(__file__).parent.parent.parent / ".package" / "portalapi.lock",
}


def _serialize_native_service_calls(func):
    import fcntl
    import functools

    @functools.wraps(func)
    def wrapper(url, *args, **kwargs):
        lock_path = None
        if isinstance(url, str):
            for base_url, path in _NATIVE_SERVICE_LOCK_FILES.items():
                if url.startswith(base_url):
                    lock_path = path
                    break
        if lock_path is None:
            return func(url, *args, **kwargs)
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with open(lock_path, "w") as lock_file:
            fcntl.flock(lock_file, fcntl.LOCK_EX)
            try:
                return func(url, *args, **kwargs)
            finally:
                fcntl.flock(lock_file, fcntl.LOCK_UN)

    return wrapper


httpx.get = _serialize_native_service_calls(httpx.get)
httpx.post = _serialize_native_service_calls(httpx.post)
httpx.put = _serialize_native_service_calls(httpx.put)
httpx.delete = _serialize_native_service_calls(httpx.delete)

_FORCE_MULTIPART = {"_multipart_": (None, b"")}


def _extract_admin_cookie(response: httpx.Response) -> str | None:
    for raw_cookie in response.headers.get_list("set-cookie"):
        jar: http.cookies.SimpleCookie = http.cookies.SimpleCookie()
        jar.load(raw_cookie)
        if _SESSION_COOKIE_NAME in jar:
            return jar[_SESSION_COOKIE_NAME].value
    return None


def ping() -> None:
    try:
        response = httpx.post(
            f"{settings.yunohost_api_base_url}/login",
            json={},
            headers=_YUNOHOST_API_HEADERS,
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("YunoHost API unreachable") from exc

    if response.status_code != 400:
        raise UpstreamProtocolError(
            f"YunoHost API /login (no credentials) returned unexpected status {response.status_code}, "
            "expected 400 — engine behavior may have changed"
        )


def login(username: str, password: str) -> str:
    try:
        response = httpx.post(
            f"{settings.yunohost_api_base_url}/login",
            json={"credentials": f"{username}:{password}"},
            headers=_YUNOHOST_API_HEADERS,
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("YunoHost API login unreachable") from exc

    if response.status_code in (400, 401):
        raise InvalidCredentialsError("YunoHost API rejected the given credentials")
    if response.status_code >= 400:
        raise UpstreamProtocolError(f"YunoHost API login returned unexpected status {response.status_code}")

    token = _extract_admin_cookie(response)
    if not token:
        raise UpstreamProtocolError("YunoHost API login succeeded but returned no session cookie")
    return token


def list_users(session_token: str) -> list[User]:
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/users",
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("YunoHost API /users unreachable") from exc

    _raise_for_admin_error(response, "YunoHost API /users")

    try:
        payload = response.json()
        raw_users = payload["users"]
    except (ValueError, KeyError) as exc:
        raise UpstreamProtocolError("YunoHost API /users returned an unexpected JSON shape") from exc

    return [
        User(username=data["username"], fullname=data["fullname"], mail=data["mail"])
        for data in raw_users.values()
    ]


def get_user(session_token: str, username: str) -> UserDetail:
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/users/{username}",
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API /users/{username} unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API /users/{username}")

    try:
        data = response.json()
        quota = data.get("mailbox-quota") or {}
        return UserDetail(
            username=data["username"],
            fullname=data["fullname"],
            mail=data["mail"],
            mail_aliases=data.get("mail-aliases", []),
            mail_forward=data.get("mail-forward", []),
            mailbox_quota_limit=quota.get("limit", "0"),
            mailbox_quota_use=quota.get("use", "?"),
        )
    except (ValueError, KeyError) as exc:
        raise UpstreamProtocolError(f"YunoHost API /users/{username} returned an unexpected JSON shape") from exc


def list_domain_names(session_token: str, full: bool = False) -> list[str]:
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/domains",
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("YunoHost API /domains unreachable") from exc

    _raise_for_admin_error(response, "YunoHost API /domains")

    try:
        domains = response.json()["domains"]
    except (ValueError, KeyError) as exc:
        raise UpstreamProtocolError("YunoHost API /domains returned an unexpected JSON shape") from exc

    if full:
        return domains
    return [d for d in domains if not d.startswith("www.")]


def get_domain_detail(session_token: str, domain: str) -> DomainDetail:
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/domains/{domain}",
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API /domains/{domain} unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API /domains/{domain}")

    try:
        data = response.json()
        cert = data.get("certificate") or {}
        return DomainDetail(
            name=domain,
            certificate=DomainCertificate(
                CA_type=cert.get("CA_type", "unknown"),
                validity=cert.get("validity", 0),
                style=cert.get("style", "danger"),
                summary=cert.get("summary", ""),
                ACME_eligible=cert.get("ACME_eligible"),
                has_wildcards=bool(cert.get("has_wildcards", False)),
            ),
            registrar=data.get("registrar") or "",
            apps=[DomainApp(id=a["id"], name=a["name"], path=a.get("path", "")) for a in data.get("apps", [])],
            main=bool(data.get("main", False)),
            topest_parent=data.get("topest_parent"),
        )
    except (ValueError, KeyError, TypeError) as exc:
        raise UpstreamProtocolError(f"YunoHost API /domains/{domain} returned an unexpected JSON shape") from exc


def get_domain_config(session_token: str, domain: str) -> dict:
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/domains/{domain}/config",
            params={"full": ""},
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API /domains/{domain}/config unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API /domains/{domain}/config")
    try:
        return response.json() or {}
    except ValueError:
        return {}


def get_domain_dns_suggestion(session_token: str, domain: str) -> str:
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/domains/{domain}/dns/suggest",
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API /domains/{domain}/dns/suggest unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API /domains/{domain}/dns/suggest")
    try:
        data = response.json()
        return data if isinstance(data, str) else str(data)
    except ValueError:
        return response.text


def set_domain_config(session_token: str, domain: str, panel_key: str, args: str) -> dict:
    try:
        response = httpx.put(
            f"{settings.yunohost_api_base_url}/domains/{domain}/config/{panel_key}",
            data={"args": args},
            files=_FORCE_MULTIPART,
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API PUT /domains/{domain}/config/{panel_key} unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API PUT /domains/{domain}/config/{panel_key}")
    try:
        return response.json() or {}
    except ValueError:
        return {}


def set_main_domain(session_token: str, domain: str) -> None:
    try:
        response = httpx.put(
            f"{settings.yunohost_api_base_url}/domains/{domain}/main",
            json={"new_main_domain": domain},
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=_HEAVY_DOMAIN_OP_TIMEOUT_SECONDS,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API PUT /domains/{domain}/main unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API PUT /domains/{domain}/main")


_CERTIFICATE_TIMEOUT_SECONDS = 300.0

_HEAVY_DOMAIN_OP_TIMEOUT_SECONDS = 60.0


def install_domain_certificate(
    session_token: str, domain: str, force: bool = False, self_signed: bool = False, no_checks: bool = False
) -> None:
    body: dict = {"domain_list": [domain]}
    if force:
        body["force"] = True
    if self_signed:
        body["self_signed"] = True
    if no_checks:
        body["no_checks"] = True
    try:
        response = httpx.put(
            f"{settings.yunohost_api_base_url}/domains/{domain}/cert",
            json=body,
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=_CERTIFICATE_TIMEOUT_SECONDS,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API PUT /domains/{domain}/cert unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API PUT /domains/{domain}/cert")


def get_certificates_status(session_token: str) -> dict:
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/domains/*/cert",
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("YunoHost API GET /domains/*/cert unreachable") from exc

    _raise_for_admin_error(response, "YunoHost API GET /domains/*/cert")

    try:
        return response.json()["certificates"]
    except (ValueError, KeyError) as exc:
        raise UpstreamProtocolError("YunoHost API /domains/*/cert returned an unexpected JSON shape") from exc


def renew_domain_certificate(
    session_token: str, domain: str, force: bool = False, email: bool = False, no_checks: bool = False
) -> None:
    body: dict = {"domain_list": [domain]}
    if force:
        body["force"] = True
    if email:
        body["email"] = True
    if no_checks:
        body["no_checks"] = True
    try:
        response = httpx.put(
            f"{settings.yunohost_api_base_url}/domains/{domain}/cert/renew",
            json=body,
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=_CERTIFICATE_TIMEOUT_SECONDS,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API PUT /domains/{domain}/cert/renew unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API PUT /domains/{domain}/cert/renew")


def add_domain(
    session_token: str,
    domain: str,
    install_letsencrypt_cert: bool = False,
    dyndns_recovery_password: str | None = None,
) -> None:
    body: dict = {"domain": domain}
    if install_letsencrypt_cert:
        body["install_letsencrypt_cert"] = True
    if dyndns_recovery_password:
        body["dyndns_recovery_password"] = dyndns_recovery_password
    try:
        response = httpx.post(
            f"{settings.yunohost_api_base_url}/domains",
            json=body,
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=_CERTIFICATE_TIMEOUT_SECONDS if install_letsencrypt_cert else _HEAVY_DOMAIN_OP_TIMEOUT_SECONDS,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("YunoHost API POST /domains unreachable") from exc

    _raise_for_admin_error(response, "YunoHost API POST /domains")


def remove_domain(
    session_token: str,
    domain: str,
    remove_apps: bool = False,
    ignore_dyndns: bool = False,
    dyndns_recovery_password: str | None = None,
) -> None:
    body: dict = {"domain": domain}
    if remove_apps:
        body["remove_apps"] = True
        body["force"] = True
    if ignore_dyndns:
        body["ignore_dyndns"] = True
    if dyndns_recovery_password:
        body["dyndns_recovery_password"] = dyndns_recovery_password
    try:
        response = httpx.request(
            "DELETE",
            f"{settings.yunohost_api_base_url}/domains/{domain}",
            json=body,
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=_HEAVY_DOMAIN_OP_TIMEOUT_SECONDS,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API DELETE /domains/{domain} unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API DELETE /domains/{domain}")


def push_domain_dns(session_token: str, domain: str, dry_run: bool = True, force: bool = False, purge: bool = False) -> dict:
    query = "&".join(
        flag for flag, enabled in (("dry_run", dry_run), ("force", force), ("purge", purge)) if enabled
    )
    url = f"{settings.yunohost_api_base_url}/domains/{domain}/dns/push"
    if query:
        url += f"?{query}"
    try:
        response = httpx.post(
            url,
            json={"domain": domain},
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API POST /domains/{domain}/dns/push unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API POST /domains/{domain}/dns/push")
    try:
        return response.json() or {}
    except ValueError:
        return {}


def list_apps(session_token: str) -> list[AppInfo]:
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/apps",
            params={"full": ""},
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("YunoHost API /apps unreachable") from exc

    if response.status_code == 401:
        raise InvalidCredentialsError("YunoHost API session token rejected")
    if response.status_code >= 400:
        raise UpstreamProtocolError(f"YunoHost API /apps returned unexpected status {response.status_code}")

    try:
        payload = response.json()
        raw_apps = payload["apps"]
    except (ValueError, KeyError) as exc:
        raise UpstreamProtocolError("YunoHost API /apps returned an unexpected JSON shape") from exc

    apps = [
        AppInfo(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            version=data["version"],
            domain_path=data.get("domain_path"),
            logo=data.get("logo"),
        )
        for data in raw_apps
    ]
    return sorted(apps, key=lambda a: a.name.lower())


def _pick_locale_text(content_per_lang: dict[str, str] | None) -> str | None:
    if not content_per_lang:
        return None
    return content_per_lang.get("fr") or content_per_lang.get("en") or next(iter(content_per_lang.values()), None)


def get_app_detail(session_token: str, app_id: str) -> AppDetail:
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/apps/{app_id}",
            params={"full": "", "with_pre_upgrade_notifications": "true"},
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API /apps/{app_id} unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API /apps/{app_id}")

    try:
        data = response.json()
        upgrade = data.get("upgrade") or {}
        notifications = (data.get("manifest") or {}).get("notifications") or {}
        post_install = _pick_locale_text((notifications.get("POST_INSTALL") or {}).get("main"))
        post_upgrade = {
            name: _pick_locale_text(content) or ""
            for name, content in (notifications.get("POST_UPGRADE") or {}).items()
        }
        pre_upgrade = {
            name: _pick_locale_text(content) or ""
            for name, content in (upgrade.get("notifications") or {}).get("PRE_UPGRADE", {}).items()
        }
        return AppDetail(
            id=data["id"],
            label=data.get("label") or data["name"],
            version=data["version"],
            description=data.get("description", ""),
            domain_path=data.get("domain_path"),
            logo=data.get("logo"),
            is_webapp=bool(data.get("is_webapp", False)),
            supports_change_url=bool(data.get("supports_change_url", False)),
            supports_purge=bool(data.get("supports_purge", False)),
            supports_config_panel=bool(data.get("supports_config_panel", False)),
            upgrade=AppUpgradeInfo(
                status=upgrade.get("status", "up_to_date"),
                message=upgrade.get("message", ""),
                current_version=upgrade.get("current_version", data["version"]),
                new_version=upgrade.get("new_version"),
                pre_upgrade_notifications=pre_upgrade,
                specific_channel=upgrade.get("specific_channel"),
                specific_channel_message=upgrade.get("specific_channel_message"),
            ),
            notification_post_install=post_install,
            notifications_post_upgrade=post_upgrade,
        )
    except (ValueError, KeyError, TypeError) as exc:
        raise UpstreamProtocolError(f"YunoHost API /apps/{app_id} returned an unexpected JSON shape") from exc


_APP_LIFECYCLE_TIMEOUT_SECONDS = 300.0


def install_app(
    session_token: str, app_id: str, label: str | None = None, args: str | None = None, force: bool = False
) -> dict:
    try:
        response = httpx.post(
            f"{settings.yunohost_api_base_url}/apps",
            json={"app": app_id, "label": label, "args": args, "force": force},
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=_APP_LIFECYCLE_TIMEOUT_SECONDS,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("YunoHost API POST /apps unreachable") from exc

    _raise_for_admin_error(response, "YunoHost API POST /apps")
    try:
        return response.json() or {}
    except ValueError:
        return {}


def remove_app(session_token: str, app_id: str, purge: bool = False) -> None:
    try:
        response = httpx.request(
            "DELETE",
            f"{settings.yunohost_api_base_url}/apps/{app_id}",
            json={"app": app_id},
            params={"purge": "1"} if purge else None,
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=_APP_LIFECYCLE_TIMEOUT_SECONDS,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API DELETE /apps/{app_id} unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API DELETE /apps/{app_id}")


def upgrade_app(session_token: str, app_id: str, force: bool = False) -> dict:
    try:
        response = httpx.put(
            f"{settings.yunohost_api_base_url}/apps/{app_id}/upgrade",
            params={"force": ""} if force else None,
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=_APP_LIFECYCLE_TIMEOUT_SECONDS,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API PUT /apps/{app_id}/upgrade unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API PUT /apps/{app_id}/upgrade")
    try:
        return response.json() or {}
    except ValueError:
        return {}


def change_app_url(session_token: str, app_id: str, domain: str, path: str) -> None:
    try:
        response = httpx.put(
            f"{settings.yunohost_api_base_url}/apps/{app_id}/changeurl",
            json={"app": app_id, "domain": domain, "path": path},
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API PUT /apps/{app_id}/changeurl unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API PUT /apps/{app_id}/changeurl")


def change_app_label(session_token: str, app_id: str, new_label: str) -> None:
    try:
        response = httpx.put(
            f"{settings.yunohost_api_base_url}/apps/{app_id}/label",
            json={"app": app_id, "new_label": new_label},
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API PUT /apps/{app_id}/label unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API PUT /apps/{app_id}/label")


def dismiss_app_notification(session_token: str, app_id: str, name: str) -> None:
    try:
        response = httpx.put(
            f"{settings.yunohost_api_base_url}/apps/{app_id}/dismiss_notification/{name}",
            json={"app": app_id, "name": name},
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(
            f"YunoHost API PUT /apps/{app_id}/dismiss_notification/{name} unreachable"
        ) from exc

    _raise_for_admin_error(response, f"YunoHost API PUT /apps/{app_id}/dismiss_notification/{name}")


def get_app_catalog(session_token: str) -> AppCatalog:
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/apps/catalog",
            params={"full": "", "with_categories": "", "with_antifeatures": ""},
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("YunoHost API /apps/catalog unreachable") from exc

    _raise_for_admin_error(response, "YunoHost API /apps/catalog")

    try:
        payload = response.json()
        raw_apps = payload["apps"]
        apps = sorted(
            (
                AppCatalogEntry(
                    id=app_id,
                    name=data["manifest"]["name"],
                    description=data["manifest"].get("description", ""),
                    level=data.get("level", -1),
                    installed=bool(data.get("installed", False)),
                    logo_hash=data.get("logo_hash"),
                    category=data.get("category"),
                    subtags=data.get("subtags", []),
                    maintained=bool(data.get("maintained", True)),
                    state=data.get("state", "working"),
                    multi_instance=bool(
                        data["manifest"].get("integration", {}).get("multi_instance", False)
                    ),
                    antifeatures=data.get("antifeatures", []),
                    potential_alternative_to=data.get("potential_alternative_to", []),
                )
                for app_id, data in raw_apps.items()
            ),
            key=lambda a: a.name.lower(),
        )
        categories = [
            AppCatalogCategory(
                id=c["id"],
                title=c.get("title", c["id"]),
                description=c.get("description", ""),
                icon=c.get("icon", ""),
                subtags=[AppCatalogSubtag(id=s["id"], title=s.get("title", s["id"])) for s in c.get("subtags", [])],
            )
            for c in payload.get("categories", [])
        ]
        antifeatures = [
            AppCatalogAntifeature(
                id=a["id"],
                title=a.get("title") or a["id"],
                description=a.get("description") or "",
            )
            for a in payload.get("antifeatures", [])
        ]
        return AppCatalog(apps=apps, categories=categories, antifeatures=antifeatures)
    except (ValueError, KeyError, TypeError) as exc:
        raise UpstreamProtocolError("YunoHost API /apps/catalog returned an unexpected JSON shape") from exc


def get_app_manifest(session_token: str, app_id: str) -> AppManifest:
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/apps/manifest",
            params={"app": app_id},
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("YunoHost API /apps/manifest unreachable") from exc

    _raise_for_admin_error(response, "YunoHost API /apps/manifest")

    try:
        data = response.json()
        description = data.get("description", "")
        if isinstance(description, dict):
            description = _pick_locale_text(description) or ""
        upstream = data.get("upstream") or {}
        return AppManifest(
            id=data["id"],
            name=data["name"],
            description=description,
            version=data.get("version", ""),
            install=data.get("install", []),
            requirements=data.get("requirements", {}),
            upstream=AppUpstreamInfo(
                license=upstream.get("license"),
                website=upstream.get("website"),
                admindoc=upstream.get("admindoc"),
                userdoc=upstream.get("userdoc"),
                code=upstream.get("code"),
            ),
        )
    except (ValueError, KeyError, TypeError) as exc:
        raise UpstreamProtocolError("YunoHost API /apps/manifest returned an unexpected JSON shape") from exc


def list_app_actions(session_token: str, app_id: str) -> dict:
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/apps/{app_id}/actions",
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API /apps/{app_id}/actions unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API /apps/{app_id}/actions")
    try:
        return response.json() or {}
    except ValueError:
        return {}


def run_app_action(session_token: str, app_id: str, action_id: str, args: str | None = None) -> dict:
    body = {"app": app_id, "action": action_id}
    if args:
        body["args"] = args
    try:
        response = httpx.put(
            f"{settings.yunohost_api_base_url}/apps/{app_id}/actions/{action_id}",
            json=body,
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=_APP_LIFECYCLE_TIMEOUT_SECONDS,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API PUT /apps/{app_id}/actions/{action_id} unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API PUT /apps/{app_id}/actions/{action_id}")
    try:
        return response.json() or {}
    except ValueError:
        return {}


def get_app_config(session_token: str, app_id: str) -> dict:
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/apps/{app_id}/config",
            params={"full": ""},
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API /apps/{app_id}/config unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API /apps/{app_id}/config")
    try:
        return response.json() or {}
    except ValueError:
        return {}


def set_app_config(session_token: str, app_id: str, panel_key: str, args: str) -> dict:
    try:
        response = httpx.put(
            f"{settings.yunohost_api_base_url}/apps/{app_id}/config/{panel_key}",
            data={"args": args},
            files=_FORCE_MULTIPART,
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=_APP_LIFECYCLE_TIMEOUT_SECONDS,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API PUT /apps/{app_id}/config/{panel_key} unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API PUT /apps/{app_id}/config/{panel_key}")
    try:
        return response.json() or {}
    except ValueError:
        return {}


def list_permissions(session_token: str) -> dict[str, PermissionInfo]:
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/users/permissions",
            params={"full": ""},
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("YunoHost API /users/permissions unreachable") from exc

    if response.status_code == 401:
        raise InvalidCredentialsError("YunoHost API session token rejected")
    if response.status_code >= 400:
        raise UpstreamProtocolError(
            f"YunoHost API /users/permissions returned unexpected status {response.status_code}"
        )

    try:
        raw = response.json()["permissions"]
    except (ValueError, KeyError) as exc:
        raise UpstreamProtocolError("YunoHost API /users/permissions returned an unexpected JSON shape") from exc

    return {
        name: PermissionInfo(
            label=data.get("label", name),
            url=data.get("url"),
            allowed=data.get("allowed", []),
            description=data.get("description"),
            order=data.get("order"),
            show_tile=data.get("show_tile"),
            hide_from_public=data.get("hide_from_public"),
            protected=data.get("protected"),
            logo_hash=data.get("logo_hash"),
            corresponding_users=data.get("corresponding_users", []),
            additional_urls=data.get("additional_urls", []),
        )
        for name, data in raw.items()
    }


def update_permission(
    session_token: str, permission: str, add: list[str] | None = None, remove: list[str] | None = None
) -> None:
    for group in add or []:
        _update_permission_group(session_token, permission, "add", group)
    for group in remove or []:
        _update_permission_group(session_token, permission, "remove", group)


def _update_permission_group(session_token: str, permission: str, action: str, group: str) -> None:
    try:
        response = httpx.put(
            f"{settings.yunohost_api_base_url}/users/permissions/{permission}/{action}/{group}",
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(
            f"YunoHost API /users/permissions/{permission}/{action}/{group} unreachable"
        ) from exc

    _raise_for_admin_error(response, f"YunoHost API /users/permissions/{permission}/{action}/{group}")


def list_groups_full(session_token: str) -> list[GroupInfo]:
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/users/groups",
            params={"full": "", "include_primary_groups": ""},
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("YunoHost API /users/groups (full) unreachable") from exc

    if response.status_code == 401:
        raise InvalidCredentialsError("YunoHost API session token rejected")
    if response.status_code >= 400:
        raise UpstreamProtocolError(
            f"YunoHost API /users/groups (full) returned unexpected status {response.status_code}"
        )

    try:
        raw = response.json()["groups"]
    except (ValueError, KeyError) as exc:
        raise UpstreamProtocolError("YunoHost API /users/groups (full) returned an unexpected JSON shape") from exc

    return [
        GroupInfo(
            name=name,
            members=data.get("members", []),
            permissions=data.get("permissions", []),
            is_special=name in _SPECIAL_GROUPS,
        )
        for name, data in raw.items()
    ]


def create_group(session_token: str, groupname: str) -> None:
    try:
        response = httpx.post(
            f"{settings.yunohost_api_base_url}/users/groups",
            json={"groupname": groupname},
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("YunoHost API /users/groups (create) unreachable") from exc

    _raise_for_admin_error(response, "YunoHost API /users/groups (create)")


def delete_group(session_token: str, groupname: str) -> None:
    try:
        response = httpx.delete(
            f"{settings.yunohost_api_base_url}/users/groups/{groupname}",
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API /users/groups/{groupname} unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API /users/groups/{groupname} (delete)")


def update_group_members(
    session_token: str, group: str, add: list[str] | None = None, remove: list[str] | None = None
) -> None:
    for user in add or []:
        _update_group_member(session_token, group, "add", user)
    for user in remove or []:
        _update_group_member(session_token, group, "remove", user)


def _update_group_member(session_token: str, group: str, action: str, user: str) -> None:
    try:
        response = httpx.put(
            f"{settings.yunohost_api_base_url}/users/groups/{group}/{action}/{user}",
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API /users/groups/{group}/{action}/{user} unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API /users/groups/{group}/{action}/{user}")


_STATUS_SEVERITY = {"SUCCESS": 0, "INFO": 0, "WARNING": 1, "ERROR": 2}
_SEVERITY_TO_STATUS = {0: "SUCCESS", 1: "WARNING", 2: "ERROR"}

_DIAGNOSIS_RUN_TIMEOUT_SECONDS = 120.0


def run_diagnosis(session_token: str, category: str | None = None) -> None:
    try:
        response = httpx.put(
            f"{settings.yunohost_api_base_url}/diagnosis/run" + ("?force" if category else ""),
            json={"categories": [category]} if category else {},
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=_DIAGNOSIS_RUN_TIMEOUT_SECONDS,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("YunoHost API /diagnosis/run unreachable") from exc

    if response.status_code >= 400:
        logger.warning(
            "YunoHost API /diagnosis/run: status=%s url=%s body=%r",
            response.status_code, response.url, response.text[:2000],
        )

    _raise_for_admin_error(response, "YunoHost API /diagnosis/run")
    get_diagnosis.cache_clear()


@_ttl_cache(21600)
def get_diagnosis(session_token: str) -> list[DiagnosisReport]:
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/diagnosis",
            params={"full": ""},
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("YunoHost API /diagnosis unreachable") from exc

    if response.status_code == 401:
        raise InvalidCredentialsError("YunoHost API session token rejected")
    if response.status_code >= 400:
        raise UpstreamProtocolError(f"YunoHost API /diagnosis returned unexpected status {response.status_code}")

    try:
        payload = response.json()
    except ValueError as exc:
        raise UpstreamProtocolError("YunoHost API /diagnosis returned an unexpected JSON shape") from exc

    if payload is None:
        return []

    try:
        raw_reports = payload["reports"]
    except (TypeError, KeyError) as exc:
        raise UpstreamProtocolError("YunoHost API /diagnosis returned an unexpected JSON shape") from exc

    reports = []
    for raw in raw_reports:
        items = [
            DiagnosisItem(
                status=item["status"],
                summary=item["summary"],
                details=item.get("details", []),
                meta=item.get("meta", {}),
                ignored=item.get("ignored", False),
            )
            for item in raw.get("items", [])
        ]
        active_items = [i for i in items if not i.ignored]
        worst = max((_STATUS_SEVERITY.get(i.status, 0) for i in active_items), default=0)
        reports.append(
            DiagnosisReport(
                id=raw["id"],
                description=raw["description"],
                status=_SEVERITY_TO_STATUS[worst],
                items=items,
                last_execution=raw.get("timestamp"),
                error_count=sum(1 for i in active_items if i.status == "ERROR"),
                warning_count=sum(1 for i in active_items if i.status == "WARNING"),
                ignored_count=sum(1 for i in items if i.ignored),
            )
        )
    return reports


def share_diagnosis_yunopaste(session_token: str) -> str:
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/diagnosis",
            params={"share": ""},
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=30.0,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("YunoHost API /diagnosis?share unreachable") from exc

    _raise_for_admin_error(response, "YunoHost API /diagnosis?share")

    try:
        return response.json()["url"]
    except (ValueError, KeyError) as exc:
        raise UpstreamProtocolError("YunoHost API /diagnosis?share returned an unexpected JSON shape") from exc


def ignore_diagnosis_item(session_token: str, category: str, meta: dict) -> None:
    _set_diagnosis_item_ignored(session_token, "ignore", category, meta)


def unignore_diagnosis_item(session_token: str, category: str, meta: dict) -> None:
    _set_diagnosis_item_ignored(session_token, "unignore", category, meta)


def _set_diagnosis_item_ignored(session_token: str, action: str, category: str, meta: dict) -> None:
    filter_ = [category] + [f"{k}={v}" for k, v in meta.items()]
    try:
        response = httpx.put(
            f"{settings.yunohost_api_base_url}/diagnosis/{action}",
            json={"filter": filter_},
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API /diagnosis/{action} unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API /diagnosis/{action}")
    get_diagnosis.cache_clear()


def _raise_for_admin_error(response: httpx.Response, context: str) -> None:
    if response.status_code == 401:
        raise InvalidCredentialsError("YunoHost API session token rejected")
    if response.status_code >= 400:
        body: dict = {}
        try:
            body = response.json() or {}
        except ValueError:
            pass
        error_key = body.get("error_key")
        detail = body.get("error")
        if error_key or detail:
            raise UpstreamValidationError(
                f"{context} rejected: {error_key or detail}",
                error_key=error_key or "upstream_rejected",
                detail=detail,
            )
        logger.warning(
            "%s: status=%s body=%r", context, response.status_code, response.text[:2000]
        )
        raise UpstreamProtocolError(f"{context} returned unexpected status {response.status_code}")


def create_user(
    session_token: str,
    username: str,
    domain: str,
    password: str,
    fullname: str,
    mailbox_quota: str = "0",
) -> None:
    try:
        response = httpx.post(
            f"{settings.yunohost_api_base_url}/users",
            json={
                "username": username,
                "domain": domain,
                "password": password,
                "fullname": fullname,
                "mailbox_quota": mailbox_quota,
            },
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("YunoHost API /users (create) unreachable") from exc

    _raise_for_admin_error(response, "YunoHost API /users (create)")


def update_user(session_token: str, username: str, **fields: object) -> None:
    try:
        response = httpx.put(
            f"{settings.yunohost_api_base_url}/users/{username}",
            json={**fields, "username": username},
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API /users/{username} (update) unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API /users/{username} (update)")


def delete_user(session_token: str, username: str, purge: bool = False) -> None:
    try:
        response = httpx.request(
            "DELETE",
            f"{settings.yunohost_api_base_url}/users/{username}",
            json={"username": username, "purge": purge},
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API /users/{username} (delete) unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API /users/{username} (delete)")


def list_user_ssh_keys(session_token: str, username: str) -> list[dict[str, str]]:
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/users/ssh/keys",
            params={"username": username},
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("YunoHost API /users/ssh/keys unreachable") from exc

    _raise_for_admin_error(response, "YunoHost API /users/ssh/keys")
    try:
        return response.json()["keys"]
    except (ValueError, KeyError) as exc:
        raise UpstreamProtocolError("YunoHost API /users/ssh/keys returned an unexpected JSON shape") from exc


def add_user_ssh_key(session_token: str, username: str, key: str, comment: str | None = None) -> None:
    body: dict = {"username": username, "key": key}
    if comment:
        body["comment"] = comment
    try:
        response = httpx.post(
            f"{settings.yunohost_api_base_url}/users/ssh/key",
            json=body,
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("YunoHost API POST /users/ssh/key unreachable") from exc

    _raise_for_admin_error(response, "YunoHost API POST /users/ssh/key")


def remove_user_ssh_key(session_token: str, username: str, key: str) -> None:
    try:
        response = httpx.request(
            "DELETE",
            f"{settings.yunohost_api_base_url}/users/ssh/key",
            json={"username": username, "key": key},
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("YunoHost API DELETE /users/ssh/key unreachable") from exc

    _raise_for_admin_error(response, "YunoHost API DELETE /users/ssh/key")


def export_users_csv(session_token: str) -> str:
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/users/export",
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("YunoHost API /users/export unreachable") from exc

    _raise_for_admin_error(response, "YunoHost API /users/export")
    return response.text


def import_users_csv(
    session_token: str, filename: str, content: bytes, update: bool = False, delete: bool = False
) -> dict:
    data = {}
    if update:
        data["update"] = "true"
    if delete:
        data["delete"] = "true"
    try:
        response = httpx.post(
            f"{settings.yunohost_api_base_url}/users/import",
            data=data,
            files={"csvfile": (filename, content, "text/csv")},
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("YunoHost API /users/import unreachable") from exc

    _raise_for_admin_error(response, "YunoHost API /users/import")
    try:
        return response.json() or {}
    except ValueError:
        return {}


def get_group_mail_aliases(session_token: str, groupname: str) -> list[str]:
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/users/groups/{groupname}",
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API /users/groups/{groupname} unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API /users/groups/{groupname}")
    try:
        return response.json()["mail-aliases"]
    except (ValueError, KeyError) as exc:
        raise UpstreamProtocolError(
            f"YunoHost API /users/groups/{groupname} returned an unexpected JSON shape"
        ) from exc


def update_group_mailaliases(
    session_token: str,
    groupname: str,
    add: list[str] | None = None,
    remove: list[str] | None = None,
    force: bool = False,
) -> None:
    for alias in add or []:
        _update_group_mailalias(session_token, groupname, "add", alias, force=force)
    for alias in remove or []:
        _update_group_mailalias(session_token, groupname, "remove", alias, force=force)


def _update_group_mailalias(
    session_token: str, groupname: str, action: str, alias: str, force: bool = False
) -> None:
    body: dict[str, object] = {"groupname": groupname, "aliases": [alias]}
    if force:
        body["force"] = True
    try:
        if action == "add":
            response = httpx.put(
                f"{settings.yunohost_api_base_url}/users/groups/{groupname}/aliases/{alias}",
                json=body,
                headers=_YUNOHOST_API_HEADERS,
                cookies={_SESSION_COOKIE_NAME: session_token},
                timeout=settings.upstream_timeout_seconds,
            )
        else:
            response = httpx.request(
                "DELETE",
                f"{settings.yunohost_api_base_url}/users/groups/{groupname}/aliases/{alias}",
                json=body,
                headers=_YUNOHOST_API_HEADERS,
                cookies={_SESSION_COOKIE_NAME: session_token},
                timeout=settings.upstream_timeout_seconds,
            )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(
            f"YunoHost API /users/groups/{groupname}/aliases/{alias} unreachable"
        ) from exc

    _raise_for_admin_error(response, f"YunoHost API /users/groups/{groupname}/aliases/{alias}")


def update_permission_properties(session_token: str, permission: str, **fields: object) -> None:
    body: dict = {"permission": permission}
    for key, value in fields.items():
        if value is None:
            continue
        body[key] = "True" if value is True else "False" if value is False else value
    try:
        response = httpx.put(
            f"{settings.yunohost_api_base_url}/users/permissions/{permission}",
            json=body,
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API /users/permissions/{permission} unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API /users/permissions/{permission}")


def update_permission_logo(session_token: str, permission: str, filename: str, content: bytes) -> None:
    try:
        response = httpx.put(
            f"{settings.yunohost_api_base_url}/users/permissions/{permission}",
            files={"logo": (filename, content, "image/png")},
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API /users/permissions/{permission} (logo) unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API /users/permissions/{permission} (logo)")


@_ttl_cache(10)
def list_services(session_token: str) -> list[ServiceInfo]:
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/services",
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("YunoHost API /services unreachable") from exc

    _raise_for_admin_error(response, "YunoHost API /services")

    try:
        raw = response.json()
        services = [
            ServiceInfo(
                name=name,
                status=data.get("status", "unknown"),
                start_on_boot=data.get("start_on_boot", "unknown"),
                last_state_change=data.get("last_state_change"),
                description=data.get("description", ""),
                configuration=data.get("configuration", "unknown"),
                configuration_details=data.get("configuration-details", []),
            )
            for name, data in raw.items()
        ]
    except (ValueError, AttributeError) as exc:
        raise UpstreamProtocolError("YunoHost API /services returned an unexpected JSON shape") from exc

    return sorted(services, key=lambda s: s.name)


_SERVICE_ACTION_EXPECTED_STATE = {
    "start": ("status", ("running", "exited")),
    "restart": ("status", ("running", "exited")),
    "stop": ("status", ("dead",)),
    "enable": ("start_on_boot", ("enabled",)),
    "disable": ("start_on_boot", ("disabled",)),
}


_SERVICE_ACTION_TIMEOUT_SECONDS = 300.0


def get_service(session_token: str, name: str) -> ServiceInfo:
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/services/{name}",
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API /services/{name} unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API /services/{name}")

    try:
        data = response.json()
        return ServiceInfo(
            name=name,
            status=data.get("status", "unknown"),
            start_on_boot=data.get("start_on_boot", "unknown"),
            last_state_change=data.get("last_state_change"),
            description=data.get("description", ""),
            configuration=data.get("configuration", "unknown"),
            configuration_details=data.get("configuration-details", []),
        )
    except (ValueError, AttributeError) as exc:
        raise UpstreamProtocolError(f"YunoHost API /services/{name} returned an unexpected JSON shape") from exc


def _service_state_matches(session_token: str, name: str, action: str) -> bool:
    field, expected = _SERVICE_ACTION_EXPECTED_STATE[action]
    try:
        check = httpx.get(
            f"{settings.yunohost_api_base_url}/services/{name}",
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
        return check.status_code == 200 and check.json().get(field) in expected
    except (httpx.HTTPError, ValueError):
        return False


def _service_action(session_token: str, name: str, action: str) -> None:
    try:
        response = httpx.put(
            f"{settings.yunohost_api_base_url}/services/{name}/{action}",
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=_SERVICE_ACTION_TIMEOUT_SECONDS,
        )
    except httpx.HTTPError as exc:
        if _service_state_matches(session_token, name, action):
            return
        raise UpstreamUnavailableError(f"YunoHost API /services/{name}/{action} unreachable") from exc

    if response.status_code >= 400 and response.status_code != 401:
        error_key = None
        try:
            error_key = response.json().get("error_key")
        except ValueError:
            pass

        if not error_key:
            if _service_state_matches(session_token, name, action):
                return

    _raise_for_admin_error(response, f"YunoHost API /services/{name}/{action}")


def start_service(session_token: str, name: str) -> None:
    _service_action(session_token, name, "start")
    list_services.cache_clear()


def stop_service(session_token: str, name: str) -> None:
    _service_action(session_token, name, "stop")
    list_services.cache_clear()


def restart_service(session_token: str, name: str) -> None:
    _service_action(session_token, name, "restart")
    list_services.cache_clear()


def enable_service(session_token: str, name: str) -> None:
    _service_action(session_token, name, "enable")
    list_services.cache_clear()


def disable_service(session_token: str, name: str) -> None:
    _service_action(session_token, name, "disable")
    list_services.cache_clear()


def get_service_log(session_token: str, name: str, number: int = 50) -> dict[str, list[str]]:
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/services/{name}/log",
            params={"number": number},
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API /services/{name}/log unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API /services/{name}/log")

    try:
        return response.json()
    except ValueError as exc:
        raise UpstreamProtocolError(f"YunoHost API /services/{name}/log returned an unexpected JSON shape") from exc


def list_logs(session_token: str, limit: int = 50) -> list[LogEntry]:
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/logs",
            params={"limit": limit, "with_details": ""},
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("YunoHost API /logs unreachable") from exc

    _raise_for_admin_error(response, "YunoHost API /logs")

    try:
        raw = response.json()["operation"]
    except (ValueError, KeyError) as exc:
        raise UpstreamProtocolError("YunoHost API /logs returned an unexpected JSON shape") from exc

    return [
        LogEntry(
            name=entry["name"],
            description=entry.get("description", entry["name"]),
            success=entry.get("success", "?"),
            started_at=entry.get("started_at"),
        )
        for entry in raw
    ]


def get_log(session_token: str, name: str, number: int = 50) -> LogDetail:
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/logs/{name}",
            params={"filter_irrelevant": "", "with_suboperations": "", "number": number},
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API /logs/{name} unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API /logs/{name}")

    try:
        data = response.json()
        metadata = data.get("metadata") or {}
        raw_logs = data.get("logs", [])
        suboperations = [
            LogSuboperation(
                name=sub["name"], description=sub.get("description", sub["name"]), success=sub.get("success", "?")
            )
            for sub in (metadata.get("suboperations") or [])
        ]
        return LogDetail(
            name=data.get("name", name),
            description=data.get("description", name),
            path=data.get("log_path"),
            started_at=metadata.get("started_at"),
            ended_at=metadata.get("ended_at"),
            error=bool(metadata.get("error")),
            suboperations=suboperations,
            logs=raw_logs,
            more_logs_available=len(raw_logs) == number,
        )
    except (ValueError, KeyError) as exc:
        raise UpstreamProtocolError(f"YunoHost API /logs/{name} returned an unexpected JSON shape") from exc


_LOG_SHARE_TIMEOUT_SECONDS = 40.0


def share_log(session_token: str, name: str) -> str:
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/logs/{name}/share",
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=_LOG_SHARE_TIMEOUT_SECONDS,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API /logs/{name}/share unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API /logs/{name}/share")

    try:
        return response.json()["url"]
    except (ValueError, KeyError) as exc:
        raise UpstreamProtocolError(f"YunoHost API /logs/{name}/share returned an unexpected JSON shape") from exc


def list_firewall(session_token: str) -> FirewallRules:
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/firewall",
            params={"raw": ""},
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("YunoHost API /firewall unreachable") from exc

    _raise_for_admin_error(response, "YunoHost API /firewall")

    try:
        data = response.json()
        return FirewallRules(
            tcp=[
                FirewallPort(port=port, open=info["open"], upnp=info["upnp"], comment=info.get("comment", ""))
                for port, info in data.get("tcp", {}).items()
            ],
            udp=[
                FirewallPort(port=port, open=info["open"], upnp=info["upnp"], comment=info.get("comment", ""))
                for port, info in data.get("udp", {}).items()
            ],
            upnp_enabled=bool(data.get("router_forwarding_upnp", False)),
        )
    except (ValueError, KeyError, AttributeError) as exc:
        raise UpstreamProtocolError("YunoHost API /firewall returned an unexpected JSON shape") from exc


_UPNP_TIMEOUT_SECONDS = 40.0


def open_firewall_port(session_token: str, protocol: str, port: int | str, comment: str = "", upnp: bool = False) -> None:
    params: dict[str, str] = {"comment": comment}
    if upnp:
        params["upnp"] = ""
    try:
        response = httpx.put(
            f"{settings.yunohost_api_base_url}/firewall/{protocol}/open/{port}",
            params=params,
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=_UPNP_TIMEOUT_SECONDS if upnp else settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API /firewall/{protocol}/open/{port} unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API /firewall/{protocol}/open/{port}")


def close_firewall_port(session_token: str, protocol: str, port: int | str, upnp_only: bool = False) -> None:
    params: dict[str, str] = {}
    if upnp_only:
        params["upnp_only"] = ""
    try:
        response = httpx.put(
            f"{settings.yunohost_api_base_url}/firewall/{protocol}/close/{port}",
            params=params,
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API /firewall/{protocol}/close/{port} unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API /firewall/{protocol}/close/{port}")


def delete_firewall_port(session_token: str, protocol: str, port: int | str) -> None:
    try:
        response = httpx.put(
            f"{settings.yunohost_api_base_url}/firewall/{protocol}/delete/{port}",
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API /firewall/{protocol}/delete/{port} unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API /firewall/{protocol}/delete/{port}")


def set_upnp(session_token: str, enabled: bool) -> None:
    action = "enable" if enabled else "disable"
    try:
        response = httpx.put(
            f"{settings.yunohost_api_base_url}/firewall/upnp/{action}",
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=_UPNP_TIMEOUT_SECONDS,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API /firewall/upnp/{action} unreachable") from exc

    if action == "enable" and response.status_code >= 400:
        error_key = None
        try:
            error_key = response.json().get("error_key")
        except ValueError:
            pass
        if not error_key:
            raise UpstreamValidationError(
                "YunoHost API /firewall/upnp/enable rejected: upnp_port_open_failed",
                error_key="upnp_port_open_failed",
            )

    _raise_for_admin_error(response, f"YunoHost API /firewall/upnp/{action}")


def list_diagnosis_categories(session_token: str) -> list[str]:
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/diagnosis/categories",
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("YunoHost API /diagnosis/categories unreachable") from exc

    _raise_for_admin_error(response, "YunoHost API /diagnosis/categories")

    try:
        return response.json()["categories"]
    except (ValueError, KeyError) as exc:
        raise UpstreamProtocolError(
            "YunoHost API /diagnosis/categories returned an unexpected JSON shape"
        ) from exc


def list_disks(session_token: str) -> list[DiskInfo]:
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/storage/disk/list",
            params={"with_info": "", "human_readable_size": ""},
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("YunoHost API /storage/disk/list unreachable") from exc

    _raise_for_admin_error(response, "YunoHost API /storage/disk/list")

    try:
        disks = response.json()["disks"]
        return [
            DiskInfo(
                name=d["name"],
                model=d.get("model", ""),
                serial=d.get("serial", ""),
                removable=d.get("removable", False),
                size=d.get("size", ""),
                smart_status=d.get("smartStatus", "UNKNOWN"),
                connection_bus=d.get("connectionBus"),
                type=d.get("type", ""),
                rpm=d.get("rpm"),
            )
            for d in disks
        ]
    except (ValueError, KeyError, TypeError) as exc:
        raise UpstreamProtocolError(
            "YunoHost API /storage/disk/list returned an unexpected JSON shape"
        ) from exc


_SMARTCTL_TIMEOUT_SECONDS = 10


def get_disk_smart(session_token: str, name: str) -> SmartReport:
    list_disks(session_token)

    device = f"/dev/{name}"
    try:
        result = subprocess.run(
            ["sudo", "-n", "smartctl", "-a", "-j", device],
            capture_output=True, text=True, timeout=_SMARTCTL_TIMEOUT_SECONDS,
        )
        data = json.loads(result.stdout)
    except (subprocess.SubprocessError, ValueError, OSError):
        return SmartReport(name=name, available=False, unavailable_reason="lecture SMART impossible")

    smart_support = data.get("smart_support", {})
    if not smart_support.get("available", False):
        return SmartReport(
            name=name, available=False,
            unavailable_reason="le disque ne prend pas en charge SMART (fréquent sur disque virtuel)",
        )

    smart_status = data.get("smart_status", {})
    power_on_time = data.get("power_on_time", {})
    temperature = data.get("temperature", {})

    attributes = [
        SmartAttribute(
            id=a.get("id", 0),
            name=a.get("name", ""),
            value=a.get("value", 0),
            worst=a.get("worst", 0),
            threshold=a.get("thresh", 0),
            raw_value=str(a.get("raw", {}).get("string", a.get("raw", {}).get("value", ""))),
            when_failed=a.get("when_failed", ""),
        )
        for a in data.get("ata_smart_attributes", {}).get("table", [])
    ]

    nvme_log = data.get("nvme_smart_health_information_log", {})

    power_on_hours = power_on_time.get("hours")
    if power_on_hours is None:
        power_on_hours = nvme_log.get("power_on_hours")

    power_cycle_count = data.get("power_cycle_count")
    if power_cycle_count is None:
        power_cycle_count = nvme_log.get("power_cycles")

    return SmartReport(
        name=name,
        available=True,
        passed=smart_status.get("passed"),
        temperature_celsius=temperature.get("current"),
        power_on_hours=power_on_hours,
        power_cycle_count=power_cycle_count,
        attributes=attributes,
        nvme_percentage_used=nvme_log.get("percentage_used"),
        nvme_media_errors=nvme_log.get("media_errors"),
        nvme_unsafe_shutdowns=nvme_log.get("unsafe_shutdowns"),
        nvme_data_units_read=nvme_log.get("data_units_read"),
        nvme_data_units_written=nvme_log.get("data_units_written"),
    )


_MOUNT_FSTYPE_DENYLIST = {
    "tmpfs", "devtmpfs", "proc", "sysfs", "cgroup", "cgroup2", "pstore",
    "bpf", "tracefs", "debugfs", "mqueue", "hugetlbfs", "devpts",
    "securityfs", "autofs", "overlay", "squashfs", "efivarfs", "configfs",
    "fusectl", "binfmt_misc", "rpc_pipefs", "nsfs",
}

_MOUNTPOINT_LABELS = {
    "/": "Disque système",
    "/boot": "Démarrage",
    "/boot/efi": "Démarrage (EFI)",
    "/home": "Dossiers utilisateurs",
    "/var": "Données applicatives",
    "/opt": "Applications installées",
    "/srv": "Données de service",
    "/tmp": "Fichiers temporaires",
}

_CONSUMER_CANDIDATES = {
    "/var/www": "Sites web et fichiers d'apps",
    "/home": "Dossiers utilisateurs",
    "/var/lib/docker": "Conteneurs Docker",
    "/var/log": "Journaux système",
    "/opt/yunohost": "Applications Wappos",
    "/var/mail": "Boîtes mail (stockage local)",
    "/var/lib/mysql": "Base de données MySQL/MariaDB",
    "/var/backups": "Sauvegardes",
    "/root": "Fichiers de l'administrateur",
}

_DU_TIMEOUT_SECONDS = 5


def _human_bytes(n: int) -> str:
    size = float(n)
    for unit in ("o", "Ko", "Mo", "Go", "To", "Po"):
        if size < 1024 or unit == "Po":
            return f"{size:.1f} {unit}" if unit != "o" else f"{int(size)} {unit}"
        size /= 1024
    return f"{size:.1f} Po"


def _human_uptime(seconds: int) -> str:
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, _ = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days} j")
    if hours or days:
        parts.append(f"{hours} h")
    parts.append(f"{minutes} min")
    return " ".join(parts)


def _read_proc_meminfo() -> dict[str, int]:
    values: dict[str, int] = {}
    with open("/proc/meminfo", "r", encoding="utf-8") as f:
        for line in f:
            parts = line.split(":")
            if len(parts) != 2:
                continue
            key = parts[0].strip()
            digits = parts[1].strip().split()[0]
            try:
                values[key] = int(digits) * 1024
            except ValueError:
                continue
    return values


def get_system_health(session_token: str) -> SystemHealth:
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/versions",
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("YunoHost API /versions unreachable") from exc
    _raise_for_admin_error(response, "YunoHost API /versions")

    with open("/proc/loadavg", "r", encoding="utf-8") as f:
        load_parts = f.read().split()
    load_1, load_5, load_15 = float(load_parts[0]), float(load_parts[1]), float(load_parts[2])

    with open("/proc/uptime", "r", encoding="utf-8") as f:
        uptime_seconds = int(float(f.read().split()[0]))

    mem = _read_proc_meminfo()
    ram_total = mem.get("MemTotal", 0)
    ram_available = mem.get("MemAvailable", 0)
    ram_used = max(ram_total - ram_available, 0)
    swap_total = mem.get("SwapTotal", 0)
    swap_free = mem.get("SwapFree", 0)
    swap_used = max(swap_total - swap_free, 0)

    os_name = ""
    try:
        with open("/etc/os-release", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    os_name = line.split("=", 1)[1].strip().strip('"')
                    break
    except OSError:
        pass

    uname = os.uname()

    return SystemHealth(
        hostname=socket.gethostname(),
        os_name=os_name or uname.sysname,
        kernel=uname.release,
        cpu_count=os.cpu_count() or 1,
        load_1min=load_1,
        load_5min=load_5,
        load_15min=load_15,
        uptime_seconds=uptime_seconds,
        uptime_human=_human_uptime(uptime_seconds),
        reboot_required=os.path.exists("/var/run/reboot-required"),
        ram_total_bytes=ram_total,
        ram_used_bytes=ram_used,
        ram_available_bytes=ram_available,
        ram_used_percent=round((ram_used / ram_total) * 100, 1) if ram_total else 0.0,
        ram_total_human=_human_bytes(ram_total),
        ram_used_human=_human_bytes(ram_used),
        ram_available_human=_human_bytes(ram_available),
        swap_total_bytes=swap_total,
        swap_used_bytes=swap_used,
        swap_used_percent=round((swap_used / swap_total) * 100, 1) if swap_total else 0.0,
        swap_total_human=_human_bytes(swap_total),
        swap_used_human=_human_bytes(swap_used),
    )


_WAPPOS_STANDALONE_MANIFESTS = {
    "wappos_api": "/opt/yunohost/wappos_api/.package/manifest.toml",
    "wappos_admin": "/opt/yunohost/wappos_admin/.package/manifest.toml",
    "wappos_portal": "/opt/yunohost/wappos_portal/.package/manifest.toml",
}


def _read_manifest_via_sudo(path: str) -> dict | None:
    try:
        result = subprocess.run(
            ["sudo", "-n", "cat", path],
            capture_output=True,
            timeout=_DU_TIMEOUT_SECONDS,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    if result.returncode != 0 or not result.stdout:
        return None
    try:
        return tomllib.loads(result.stdout.decode("utf-8"))
    except (tomllib.TOMLDecodeError, UnicodeDecodeError):
        return None


def list_wappos_component_versions(session_token: str) -> list[WapposComponentVersion]:
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/versions",
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("YunoHost API /versions unreachable") from exc
    _raise_for_admin_error(response, "YunoHost API /versions")

    versions: list[WapposComponentVersion] = []
    for app_id, manifest_path in _WAPPOS_STANDALONE_MANIFESTS.items():
        manifest = _read_manifest_via_sudo(manifest_path)
        if not manifest:
            continue
        versions.append(
            WapposComponentVersion(
                id=app_id,
                name=manifest.get("name", app_id),
                version=manifest.get("version", "?"),
            )
        )
    return versions


def _mountpoint_label(mountpoint: str) -> str:
    return _MOUNTPOINT_LABELS.get(mountpoint, mountpoint)


def _dir_size_bytes(path: str) -> int | None:
    try:
        result = subprocess.run(
            ["sudo", "-n", "du", "-sb", path],
            capture_output=True,
            text=True,
            timeout=_DU_TIMEOUT_SECONDS,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    if not result.stdout:
        return None
    try:
        return int(result.stdout.split()[0])
    except (ValueError, IndexError):
        return None


_CONSUMER_SIZES_CACHE_FILE = Path(__file__).parent.parent.parent / ".package" / "consumer_sizes_cache.json"
_CONSUMER_SIZES_CACHE_TTL_SECONDS = 300


def _read_consumer_sizes_cache() -> list[tuple[str, str, int | None]] | None:
    try:
        cached = json.loads(_CONSUMER_SIZES_CACHE_FILE.read_text())
    except (OSError, ValueError):
        return None
    if time.time() - cached.get("fetched_at", 0) >= _CONSUMER_SIZES_CACHE_TTL_SECONDS:
        return None
    return [tuple(entry) for entry in cached.get("sizes", [])]


def _write_consumer_sizes_cache(result: list[tuple[str, str, int | None]]) -> None:
    try:
        _CONSUMER_SIZES_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = _CONSUMER_SIZES_CACHE_FILE.with_suffix(".tmp")
        tmp_path.write_text(json.dumps({"fetched_at": time.time(), "sizes": result}))
        os.replace(tmp_path, _CONSUMER_SIZES_CACHE_FILE)
    except OSError:
        pass


def _cached_consumer_sizes(force: bool = False) -> list[tuple[str, str, int | None]]:
    if not force:
        cached = _read_consumer_sizes_cache()
        if cached is not None:
            return cached
    candidates = [
        (path, label) for path, label in _CONSUMER_CANDIDATES.items() if os.path.isdir(path)
    ]
    with ThreadPoolExecutor(max_workers=max(1, len(candidates))) as pool:
        sizes = list(pool.map(lambda pl: _dir_size_bytes(pl[0]), candidates))
    result = [(path, label, size) for (path, label), size in zip(candidates, sizes)]
    _write_consumer_sizes_cache(result)
    return result


def _best_matching_mountpoint(path: str, mountpoints: list[str]) -> str | None:
    best: str | None = None
    for mp in mountpoints:
        if path == mp or path.startswith(mp.rstrip("/") + "/"):
            if best is None or len(mp) > len(best):
                best = mp
    return best


@_ttl_cache(10)
def list_mounts(session_token: str) -> list[MountInfo]:
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/storage/disk/list",
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("YunoHost API /storage/disk/list unreachable") from exc
    _raise_for_admin_error(response, "YunoHost API /storage/disk/list")

    mounts: list[MountInfo] = []
    seen_devices: set[str] = set()
    with open("/proc/mounts", "r", encoding="utf-8") as f:
        for line in f:
            parts = line.split()
            if len(parts) < 3:
                continue
            device, mountpoint, fstype = parts[0], parts[1], parts[2]
            if fstype in _MOUNT_FSTYPE_DENYLIST:
                continue
            if not device.startswith("/dev/"):
                continue
            if device in seen_devices:
                continue
            try:
                stat = os.statvfs(mountpoint)
            except OSError:
                continue
            total = stat.f_frsize * stat.f_blocks
            free = stat.f_frsize * stat.f_bavail
            if total == 0:
                continue
            used = total - (stat.f_frsize * stat.f_bfree)
            seen_devices.add(device)
            mounts.append(
                MountInfo(
                    mountpoint=mountpoint,
                    label=_mountpoint_label(mountpoint),
                    device=device,
                    fstype=fstype,
                    total_bytes=total,
                    used_bytes=used,
                    free_bytes=free,
                    used_percent=round((used / total) * 100, 1),
                    total_human=_human_bytes(total),
                    used_human=_human_bytes(used),
                    free_human=_human_bytes(free),
                )
            )
    mounts.sort(key=lambda m: m.mountpoint)

    mountpoints = [m.mountpoint for m in mounts]
    consumer_sizes = _cached_consumer_sizes()

    consumers_by_mount: dict[str, list[MountConsumer]] = {mp: [] for mp in mountpoints}
    for path, label, size in consumer_sizes:
        if not size:
            continue
        target_mount = _best_matching_mountpoint(path, mountpoints)
        if target_mount is None:
            continue
        consumers_by_mount[target_mount].append(
            MountConsumer(path=path, label=label, size_bytes=size, size_human=_human_bytes(size))
        )

    for m in mounts:
        m.top_consumers = sorted(
            consumers_by_mount.get(m.mountpoint, []), key=lambda c: c.size_bytes, reverse=True
        )[:5]

    return mounts


def get_global_settings(session_token: str) -> dict:
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/settings",
            params={"full": ""},
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("YunoHost API /settings unreachable") from exc

    _raise_for_admin_error(response, "YunoHost API /settings")
    try:
        return response.json() or {}
    except ValueError:
        return {}


def set_global_settings(session_token: str, panel_key: str, args: str) -> dict:
    try:
        response = httpx.put(
            f"{settings.yunohost_api_base_url}/settings/{panel_key}",
            data={"args": args},
            files=_FORCE_MULTIPART,
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API PUT /settings/{panel_key} unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API PUT /settings/{panel_key}")
    try:
        return response.json() or {}
    except ValueError:
        return {}


def reset_global_setting(session_token: str, key: str) -> None:
    try:
        response = httpx.delete(
            f"{settings.yunohost_api_base_url}/settings/{key}",
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API DELETE /settings/{key} unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API DELETE /settings/{key}")


def reset_all_global_settings(session_token: str) -> None:
    try:
        response = httpx.delete(
            f"{settings.yunohost_api_base_url}/settings",
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("YunoHost API DELETE /settings unreachable") from exc

    _raise_for_admin_error(response, "YunoHost API DELETE /settings")


def get_global_setting(session_token: str, key: str) -> dict:
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/settings/{key}",
            params={"full": ""},
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API /settings/{key} unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API /settings/{key}")
    try:
        return response.json() or {}
    except ValueError:
        return {}


def get_app_map(session_token: str, app_id: str | None = None, raw: bool = False, user: str | None = None) -> dict:
    params: dict[str, str] = {}
    if app_id:
        params["app"] = app_id
    if raw:
        params["raw"] = ""
    if user:
        params["user"] = user
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/apps/map",
            params=params,
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("YunoHost API /apps/map unreachable") from exc

    _raise_for_admin_error(response, "YunoHost API /apps/map")
    try:
        return response.json() or {}
    except ValueError:
        return {}


def app_setting(
    session_token: str, app_id: str, key: str, value: str | None = None, delete: bool = False
) -> dict:
    params: dict[str, str] = {"key": key}
    if value is not None:
        params["value"] = value
    if delete:
        params["delete"] = ""
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/apps/{app_id}/settings",
            params=params,
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API /apps/{app_id}/settings unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API /apps/{app_id}/settings")
    try:
        return {"value": response.json()}
    except ValueError:
        return {"value": None}


def app_makedefault(
    session_token: str, app_id: str, domain: str | None = None, undo: bool = False
) -> None:
    body: dict = {"app": app_id}
    if domain:
        body["domain"] = domain
    if undo:
        body["undo"] = True
    try:
        response = httpx.put(
            f"{settings.yunohost_api_base_url}/apps/{app_id}/default",
            json=body,
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API PUT /apps/{app_id}/default unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API PUT /apps/{app_id}/default")


_APP_SHELL_TIMEOUT_SECONDS = 3.0


def get_app_shell_info(session_token: str, app_id: str) -> str:
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/apps/{app_id}/shell",
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=_APP_SHELL_TIMEOUT_SECONDS,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API /apps/{app_id}/shell unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API /apps/{app_id}/shell")
    return response.text


def check_domain_url_available(session_token: str, domain: str, path: str) -> bool:
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/domain/{domain}/urlavailable",
            params={"path": path},
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API /domain/{domain}/urlavailable unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API /domain/{domain}/urlavailable")
    try:
        return bool(response.json())
    except ValueError:
        return False


def run_domain_action(session_token: str, domain: str, action_id: str, args: str | None = None) -> dict:
    body: dict = {"domain": domain, "action": action_id}
    if args:
        body["args"] = args
    try:
        response = httpx.put(
            f"{settings.yunohost_api_base_url}/domain/{domain}/actions/{action_id}",
            json=body,
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(
            f"YunoHost API PUT /domain/{domain}/actions/{action_id} unreachable"
        ) from exc

    _raise_for_admin_error(response, f"YunoHost API PUT /domain/{domain}/actions/{action_id}")
    try:
        return response.json() or {}
    except ValueError:
        return {}


def allow_firewall(
    session_token: str,
    protocol: str,
    port: int | str,
    ipv4_only: bool = False,
    ipv6_only: bool = False,
    no_upnp: bool = False,
) -> None:
    params: dict[str, str] = {}
    if ipv4_only:
        params["ipv4_only"] = ""
    if ipv6_only:
        params["ipv6_only"] = ""
    if no_upnp:
        params["no_upnp"] = ""
    try:
        response = httpx.put(
            f"{settings.yunohost_api_base_url}/firewall/{protocol}/allow/{port}",
            params=params,
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API /firewall/{protocol}/allow/{port} unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API /firewall/{protocol}/allow/{port}")


def disallow_firewall(
    session_token: str,
    protocol: str,
    port: int | str,
    ipv4_only: bool = False,
    ipv6_only: bool = False,
    upnp_only: bool = False,
) -> None:
    params: dict[str, str] = {}
    if ipv4_only:
        params["ipv4_only"] = ""
    if ipv6_only:
        params["ipv6_only"] = ""
    if upnp_only:
        params["upnp_only"] = ""
    try:
        response = httpx.put(
            f"{settings.yunohost_api_base_url}/firewall/{protocol}/disallow/{port}",
            params=params,
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API /firewall/{protocol}/disallow/{port} unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API /firewall/{protocol}/disallow/{port}")


def get_disk_info(session_token: str, name: str) -> dict:
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/storage/disk/info/{name}",
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API /storage/disk/info/{name} unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API /storage/disk/info/{name}")
    try:
        return response.json() or {}
    except ValueError:
        return {}


def list_hooks(session_token: str, action: str) -> list[str]:
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/hooks/{action}",
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API /hooks/{action} unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API /hooks/{action}")
    try:
        data = response.json()
        return data.get("hooks", []) if isinstance(data, dict) else data
    except ValueError:
        return []


_BACKUP_TIMEOUT_SECONDS = 300.0


@_ttl_cache(21600)
def list_backups(session_token: str, with_info: bool = True, human_readable: bool = False) -> dict:
    params: dict[str, str] = {}
    if with_info:
        params["with_info"] = ""
    if human_readable:
        params["human_readable"] = ""
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/backups",
            params=params,
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("YunoHost API /backups unreachable") from exc

    _raise_for_admin_error(response, "YunoHost API /backups")
    try:
        return response.json() or {}
    except ValueError:
        return {}


def get_backup_info(session_token: str, name: str, with_details: bool = True, human_readable: bool = False) -> dict:
    params: dict[str, str] = {}
    if with_details:
        params["with_details"] = ""
    if human_readable:
        params["human_readable"] = ""
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/backups/{name}",
            params=params,
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API /backups/{name} unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API /backups/{name}")
    try:
        return response.json() or {}
    except ValueError:
        return {}


def create_backup(
    session_token: str,
    name: str | None = None,
    description: str | None = None,
    system: list[str] | None = None,
    apps: list[str] | None = None,
) -> dict:
    body: dict = {}
    if name:
        body["name"] = name
    if description:
        body["description"] = description
    if system:
        body["system"] = system
    if apps:
        body["apps"] = apps
    try:
        response = httpx.post(
            f"{settings.yunohost_api_base_url}/backups",
            json=body,
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=_BACKUP_TIMEOUT_SECONDS,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("YunoHost API POST /backups unreachable") from exc

    _raise_for_admin_error(response, "YunoHost API POST /backups")
    list_backups.cache_clear()
    try:
        return response.json() or {}
    except ValueError:
        return {}


def restore_backup(
    session_token: str,
    name: str,
    system: list[str] | None = None,
    apps: list[str] | None = None,
    force: bool = False,
    no_remove_on_failure: bool = False,
) -> dict:
    body: dict = {"name": name}
    if system:
        body["system"] = system
    if apps:
        body["apps"] = apps
    if force:
        body["force"] = True
    if no_remove_on_failure:
        body["no_remove_on_failure"] = True
    try:
        response = httpx.put(
            f"{settings.yunohost_api_base_url}/backups/{name}/restore",
            json=body,
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=_BACKUP_TIMEOUT_SECONDS,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API PUT /backups/{name}/restore unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API PUT /backups/{name}/restore")
    try:
        return response.json() or {}
    except ValueError:
        return {}


def delete_backup(session_token: str, name: str) -> None:
    try:
        response = httpx.request(
            "DELETE",
            f"{settings.yunohost_api_base_url}/backups/{name}",
            json={"name": name},
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API DELETE /backups/{name} unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API DELETE /backups/{name}")
    list_backups.cache_clear()


def stream_backup_download(session_token: str, name: str):
    client = httpx.Client(timeout=_BACKUP_TIMEOUT_SECONDS)
    try:
        request_ = client.build_request(
            "GET",
            f"{settings.yunohost_api_base_url}/backups/{name}/download",
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
        )
        response = client.send(request_, stream=True)
    except httpx.HTTPError as exc:
        client.close()
        raise UpstreamUnavailableError(f"YunoHost API /backups/{name}/download unreachable") from exc

    if response.status_code >= 400:
        response.read()
        response.close()
        client.close()
        _raise_for_admin_error(response, f"YunoHost API /backups/{name}/download")

    content_type = response.headers.get("content-type", "application/octet-stream")
    content_disposition = response.headers.get("content-disposition")

    def body():
        try:
            for chunk in response.iter_bytes():
                yield chunk
        finally:
            response.close()
            client.close()

    return body(), content_type, content_disposition


_TOOLS_TIMEOUT_SECONDS = 300.0


def get_versions(session_token: str) -> dict:
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/versions",
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("YunoHost API /versions unreachable") from exc

    _raise_for_admin_error(response, "YunoHost API /versions")
    try:
        return response.json() or {}
    except ValueError:
        return {}


@_ttl_cache(86400)
def get_available_updates(session_token: str) -> dict:
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/update",
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("YunoHost API /update unreachable") from exc

    _raise_for_admin_error(response, "YunoHost API /update")
    try:
        return response.json() or {}
    except ValueError:
        return {}


def refresh_updates(session_token: str, target: str = "all", no_refresh: bool = False) -> dict:
    body: dict = {"target": target}
    if no_refresh:
        body["no_refresh"] = True
    try:
        response = httpx.put(
            f"{settings.yunohost_api_base_url}/update/{target}",
            json=body,
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=_TOOLS_TIMEOUT_SECONDS,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API PUT /update/{target} unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API PUT /update/{target}")
    get_available_updates.cache_clear()
    try:
        return response.json() or {}
    except ValueError:
        return {}


def run_upgrade(session_token: str, target: str) -> dict:
    body: dict = {"target": target}
    try:
        response = httpx.put(
            f"{settings.yunohost_api_base_url}/upgrade/{target}",
            json=body,
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=_TOOLS_TIMEOUT_SECONDS,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API PUT /upgrade/{target} unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API PUT /upgrade/{target}")
    get_available_updates.cache_clear()
    try:
        return response.json() or {}
    except ValueError:
        return {}


def list_migrations(session_token: str, pending: bool = False, done: bool = False) -> list[dict]:
    params: dict = {}
    if pending:
        params["pending"] = ""
    if done:
        params["done"] = ""
    try:
        response = httpx.get(
            f"{settings.yunohost_api_base_url}/migrations",
            params=params,
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("YunoHost API GET /migrations unreachable") from exc

    _raise_for_admin_error(response, "YunoHost API GET /migrations")

    try:
        return response.json()["migrations"]
    except (ValueError, KeyError) as exc:
        raise UpstreamProtocolError("YunoHost API /migrations returned an unexpected JSON shape") from exc


def run_migrations(
    session_token: str,
    targets: list[str] | None = None,
    skip: bool = False,
    force_rerun: bool = False,
    accept_disclaimer: bool = False,
    auto: bool = False,
) -> dict:
    body: dict = {}
    if skip:
        body["skip"] = True
    if force_rerun:
        body["force_rerun"] = True
    if accept_disclaimer:
        body["accept_disclaimer"] = True
    if auto:
        body["auto"] = True
    url = f"{settings.yunohost_api_base_url}/migrations"
    if targets:
        url = f"{url}/{','.join(targets)}"
    try:
        response = httpx.put(
            url,
            json=body,
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=_TOOLS_TIMEOUT_SECONDS,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API PUT {url} unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API PUT {url}")
    try:
        return response.json() or {}
    except ValueError:
        return {}


def regen_conf(
    session_token: str,
    names: list[str] | None = None,
    with_diff: bool = False,
    force: bool = False,
    dry_run: bool = False,
    list_pending: bool = False,
) -> dict:
    body: dict = {}
    if with_diff:
        body["with_diff"] = True
    if force:
        body["force"] = True
    if dry_run:
        body["dry_run"] = True
    if list_pending:
        body["list_pending"] = True
    url = f"{settings.yunohost_api_base_url}/regenconf"
    if names:
        body["names"] = names
        url = f"{url}/{','.join(names)}"
    try:
        response = httpx.put(
            url,
            json=body,
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=_TOOLS_TIMEOUT_SECONDS,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError(f"YunoHost API PUT {url} unreachable") from exc

    _raise_for_admin_error(response, f"YunoHost API PUT {url}")
    try:
        return response.json() or {}
    except ValueError:
        return {}


def change_root_password(session_token: str, new_password: str) -> None:
    try:
        response = httpx.put(
            f"{settings.yunohost_api_base_url}/rootpw",
            json={"new_password": new_password},
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("YunoHost API PUT /rootpw unreachable") from exc

    _raise_for_admin_error(response, "YunoHost API PUT /rootpw")


def reboot_server(session_token: str, force: bool = False) -> None:
    body: dict = {}
    if force:
        body["force"] = True
    try:
        response = httpx.put(
            f"{settings.yunohost_api_base_url}/reboot",
            json=body,
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("YunoHost API PUT /reboot unreachable") from exc

    _raise_for_admin_error(response, "YunoHost API PUT /reboot")


def shutdown_server(session_token: str, force: bool = False) -> None:
    body: dict = {}
    if force:
        body["force"] = True
    try:
        response = httpx.put(
            f"{settings.yunohost_api_base_url}/shutdown",
            json=body,
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("YunoHost API PUT /shutdown unreachable") from exc

    _raise_for_admin_error(response, "YunoHost API PUT /shutdown")


def run_postinstall(
    session_token: str,
    domain: str,
    username: str,
    fullname: str,
    password: str,
    ignore_dyndns: bool = False,
    force_diskspace: bool = False,
    i_have_read_terms_of_services: bool = False,
) -> None:
    body: dict = {
        "domain": domain,
        "username": username,
        "fullname": fullname,
        "password": password,
    }
    if ignore_dyndns:
        body["ignore_dyndns"] = True
    if force_diskspace:
        body["force_diskspace"] = True
    if i_have_read_terms_of_services:
        body["i_have_read_terms_of_services"] = True
    try:
        response = httpx.post(
            f"{settings.yunohost_api_base_url}/postinstall",
            json=body,
            headers=_YUNOHOST_API_HEADERS,
            cookies={_SESSION_COOKIE_NAME: session_token},
            timeout=_TOOLS_TIMEOUT_SECONDS,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("YunoHost API POST /postinstall unreachable") from exc

    _raise_for_admin_error(response, "YunoHost API POST /postinstall")
