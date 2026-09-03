# Auteur : Patrick Ritaine

from __future__ import annotations

import logging
import os
import re
import secrets
import time
from pathlib import Path
from typing import Any

from fastapi import Body, FastAPI, File, Form, Header, HTTPException, Request, Response, UploadFile
from fastapi.responses import StreamingResponse
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Gauge, Histogram, generate_latest, multiprocess

from wappos_api.config import settings
from wappos_api.connectors import adguard as adguard_connector
from wappos_api.connectors import admin as admin_connector
from wappos_api.connectors import domains_public as domains_public_connector
from wappos_api.connectors import portal as portal_connector
from wappos_api.errors import UpstreamValidationError, WapposApiError
from wappos_api.schemas.adguard import AdguardRewrite, AdguardRewriteRequest, AdguardStatus
from wappos_api.schemas.admin import (
    AdminLoginRequest,
    AdminTokenResponse,
    CreateUserRequest,
    UpdateUserRequest,
)
from wappos_api.schemas.app import AppCatalog, AppDetail, AppInfo, AppManifest
from wappos_api.schemas.backup import BackupCreateRequest, BackupRestoreRequest
from wappos_api.schemas.diagnosis import DiagnosisIgnoreRequest, DiagnosisReport
from wappos_api.schemas.domain import DomainCertificate, DomainDetail, LocalDomainRequest, LocalDomainResult
from wappos_api.schemas.firewall import FirewallRules
from wappos_api.schemas.group import (
    CreateGroupRequest,
    GroupAliasesUpdateRequest,
    GroupInfo,
    GroupMembersUpdateRequest,
)
from wappos_api.schemas.health import ConnectorHealth, HealthReport
from wappos_api.schemas.log import LogDetail, LogEntry
from wappos_api.schemas.permission import (
    PermissionInfo,
    PermissionPropertiesUpdateRequest,
    PermissionUpdateRequest,
)
from wappos_api.schemas.portal import PortalLoginRequest, PortalLogoutResponse, PortalTokenResponse
from wappos_api.schemas.service import ServiceInfo
from wappos_api.schemas.storage import DiskInfo, MountInfo, SmartReport
from wappos_api.schemas.system import SystemHealth, WapposComponentVersion
from wappos_api.schemas.tools import (
    Migration,
    MigrationRunRequest,
    PostinstallRequest,
    RegenConfRequest,
    RootPasswordChangeRequest,
)
from wappos_api.schemas.user import SshKey, SshKeyAddRequest, SshKeyRemoveRequest, User, UserDetail

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger("wappos_api")

app = FastAPI(title="Wappos API", version="0.1.0")

_metrics_token_file = Path(__file__).parent.parent / ".package" / "metrics_token"
if not _metrics_token_file.exists():
    _metrics_token_file.parent.mkdir(parents=True, exist_ok=True)
    _metrics_token_file.write_text(secrets.token_hex(32))
METRICS_TOKEN = _metrics_token_file.read_text().strip()

_REQUEST_COUNT = Counter(
    "wappos_api_requests_total", "Nombre de requêtes HTTP traitées",
    ["method", "endpoint", "status"],
)
_REQUEST_LATENCY = Histogram(
    "wappos_api_request_duration_seconds", "Durée des requêtes HTTP",
    ["method", "endpoint"],
)
_PROCESS_MEMORY = Gauge(
    "wappos_api_process_resident_memory_bytes", "Mémoire résidente du worker",
    multiprocess_mode="livesum",
)


def _current_rss_bytes() -> int:
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) * 1024
    except OSError:
        pass
    return 0


@app.middleware("http")
async def _record_metrics(request: Request, call_next):
    _PROCESS_MEMORY.set(_current_rss_bytes())
    if request.url.path == "/metrics":
        return await call_next(request)
    start = time.monotonic()
    response = await call_next(request)
    endpoint = request.scope.get("route").path if request.scope.get("route") else request.url.path
    _REQUEST_LATENCY.labels(method=request.method, endpoint=endpoint).observe(time.monotonic() - start)
    _REQUEST_COUNT.labels(method=request.method, endpoint=endpoint, status=response.status_code).inc()
    return response


def _generate_metrics() -> bytes:
    if os.environ.get("PROMETHEUS_MULTIPROC_DIR"):
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
        return generate_latest(registry)
    return generate_latest()


@app.get("/metrics")
def metrics(authorization: str = Header(default="")) -> Response:
    token = authorization[7:] if authorization.startswith("Bearer ") else ""
    if not secrets.compare_digest(token, METRICS_TOKEN):
        raise HTTPException(status_code=403, detail="forbidden")
    return Response(_generate_metrics(), media_type=CONTENT_TYPE_LATEST)


def _raise_as_http(exc: WapposApiError) -> None:
    if exc.status_code >= 500:
        logger.error("%s: %s (cause=%r)", exc.code, exc.message, exc.__cause__)
    body = {"code": exc.code, "message": exc.message}
    native_detail = getattr(exc, "detail", None)
    if native_detail:
        body["native_detail"] = native_detail
    raise HTTPException(status_code=exc.status_code, detail=body) from exc


_HEALTHCHECK_HOST = "localhost"


@app.get("/health", response_model=HealthReport)
def health() -> HealthReport:
    portalapi_health = _check_portalapi()
    yunohost_api_health = _check_yunohost_api()

    overall = "ok" if portalapi_health.status == "ok" and yunohost_api_health.status == "ok" else "degraded"

    return HealthReport(
        status=overall,
        portalapi=portalapi_health,
        yunohost_api=yunohost_api_health,
    )


def _check_portalapi() -> ConnectorHealth:
    try:
        portal_connector.ping(_HEALTHCHECK_HOST)
    except WapposApiError as exc:
        logger.warning("portalapi healthcheck failed: %s", exc.code)
        return ConnectorHealth(status="unreachable", detail=exc.code)
    return ConnectorHealth(status="ok")


def _check_yunohost_api() -> ConnectorHealth:
    try:
        admin_connector.ping()
    except WapposApiError as exc:
        logger.warning("YunoHost API healthcheck failed: %s", exc.code)
        return ConnectorHealth(status="unreachable", detail=exc.code)
    return ConnectorHealth(status="ok")


@app.post("/portal/login", response_model=PortalTokenResponse)
def portal_login(payload: PortalLoginRequest, x_portal_host: str = Header()) -> PortalTokenResponse:
    try:
        token, cookie = portal_connector.login(x_portal_host, payload.user, payload.password)
    except WapposApiError as exc:
        _raise_as_http(exc)
    return PortalTokenResponse(token=token, cookie=cookie)


@app.post("/portal/logout", response_model=PortalLogoutResponse)
def portal_logout(x_portal_host: str = Header(), x_portal_token: str = Header()) -> PortalLogoutResponse:
    try:
        cookie = portal_connector.logout(x_portal_host, x_portal_token)
    except WapposApiError as exc:
        _raise_as_http(exc)
    return PortalLogoutResponse(cookie=cookie)


@app.get("/portal/me")
def portal_me(x_portal_host: str = Header(), x_portal_token: str = Header()) -> dict[str, Any]:
    try:
        return portal_connector.me(x_portal_host, x_portal_token)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.put("/portal/update", status_code=204)
def portal_update(
    fields: dict[str, Any], x_portal_host: str = Header(), x_portal_token: str = Header()
) -> Response:
    try:
        portal_connector.update(x_portal_host, x_portal_token, **fields)
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)


@app.get("/portal/public")
def portal_public(x_portal_host: str = Header(), x_portal_token: str | None = Header(default=None)) -> dict[str, Any]:
    try:
        return portal_connector.public(x_portal_host, x_portal_token)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.get("/portal/domains", response_model=list[str])
def portal_domains() -> list[str]:
    try:
        return domains_public_connector.list_domain_names()
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.post("/admin/login", response_model=AdminTokenResponse)
def admin_login(payload: AdminLoginRequest) -> AdminTokenResponse:
    try:
        token = admin_connector.login(payload.user, payload.password)
    except WapposApiError as exc:
        _raise_as_http(exc)
    return AdminTokenResponse(token=token)


@app.get("/admin/users", response_model=list[User])
def admin_users(x_admin_token: str = Header()) -> list[User]:
    try:
        return admin_connector.list_users(x_admin_token)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.post("/admin/users", status_code=204)
def admin_create_user(payload: CreateUserRequest, x_admin_token: str = Header()) -> Response:
    try:
        admin_connector.create_user(
            x_admin_token,
            username=payload.username,
            domain=payload.domain,
            password=payload.password,
            fullname=payload.fullname,
            mailbox_quota=payload.mailbox_quota,
        )
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)


@app.put("/admin/users/{username}", status_code=204)
def admin_update_user(username: str, payload: UpdateUserRequest, x_admin_token: str = Header()) -> Response:
    try:
        admin_connector.update_user(x_admin_token, username, **payload.model_dump(exclude_unset=True))
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)


@app.delete("/admin/users/{username}", status_code=204)
def admin_delete_user(username: str, purge: bool = False, x_admin_token: str = Header()) -> Response:
    try:
        admin_connector.delete_user(x_admin_token, username, purge=purge)
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)


@app.get("/admin/users/{username}/ssh-keys", response_model=list[SshKey])
def admin_user_ssh_keys(username: str, x_admin_token: str = Header()) -> list[SshKey]:
    try:
        return admin_connector.list_user_ssh_keys(x_admin_token, username)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.post("/admin/users/{username}/ssh-keys", status_code=204)
def admin_add_user_ssh_key(username: str, payload: SshKeyAddRequest, x_admin_token: str = Header()) -> Response:
    try:
        admin_connector.add_user_ssh_key(x_admin_token, username, payload.key, comment=payload.comment)
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)


@app.delete("/admin/users/{username}/ssh-keys", status_code=204)
def admin_remove_user_ssh_key(
    username: str, payload: SshKeyRemoveRequest, x_admin_token: str = Header()
) -> Response:
    try:
        admin_connector.remove_user_ssh_key(x_admin_token, username, payload.key)
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)


@app.get("/admin/domains", response_model=list[str])
def admin_domains(full: bool = False, x_admin_token: str = Header()) -> list[str]:
    try:
        return admin_connector.list_domain_names(x_admin_token, full=full)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.get("/admin/domains/certificates", response_model=dict[str, DomainCertificate])
def admin_domains_certificates(x_admin_token: str = Header()) -> dict:
    try:
        return admin_connector.get_certificates_status(x_admin_token)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.get("/admin/domains/{domain}", response_model=DomainDetail)
def admin_domain_detail(domain: str, x_admin_token: str = Header()) -> DomainDetail:
    try:
        return admin_connector.get_domain_detail(x_admin_token, domain)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.get("/admin/domains/{domain}/config")
def admin_domain_config(domain: str, x_admin_token: str = Header()) -> dict:
    try:
        return admin_connector.get_domain_config(x_admin_token, domain)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.get("/admin/domains/{domain}/dns/suggest")
def admin_domain_dns_suggest(domain: str, x_admin_token: str = Header()) -> dict[str, str]:
    try:
        return {"suggestion": admin_connector.get_domain_dns_suggestion(x_admin_token, domain)}
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.put("/admin/domains/{domain}/config/{panel_key}")
def admin_set_domain_config(
    domain: str, panel_key: str, args: str = Body(..., embed=True), x_admin_token: str = Header()
) -> dict:
    try:
        return admin_connector.set_domain_config(x_admin_token, domain, panel_key, args)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.put("/admin/domains/{domain}/main", status_code=204)
def admin_set_main_domain(domain: str, x_admin_token: str = Header()) -> Response:
    try:
        admin_connector.set_main_domain(x_admin_token, domain)
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)


@app.put("/admin/domains/{domain}/cert", status_code=204)
def admin_install_domain_certificate(
    domain: str,
    force: bool = False,
    self_signed: bool = False,
    no_checks: bool = False,
    x_admin_token: str = Header(),
) -> Response:
    try:
        admin_connector.install_domain_certificate(
            x_admin_token, domain, force=force, self_signed=self_signed, no_checks=no_checks
        )
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)


@app.put("/admin/domains/{domain}/cert/renew", status_code=204)
def admin_renew_domain_certificate(
    domain: str, force: bool = False, email: bool = False, no_checks: bool = False, x_admin_token: str = Header()
) -> Response:
    try:
        admin_connector.renew_domain_certificate(x_admin_token, domain, force=force, email=email, no_checks=no_checks)
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)


@app.post("/admin/domains", status_code=204)
def admin_add_domain(
    domain: str = Body(..., embed=True),
    install_letsencrypt_cert: bool = Body(False, embed=True),
    dyndns_recovery_password: str | None = Body(None, embed=True),
    x_admin_token: str = Header(),
) -> Response:
    try:
        admin_connector.add_domain(
            x_admin_token,
            domain,
            install_letsencrypt_cert=install_letsencrypt_cert,
            dyndns_recovery_password=dyndns_recovery_password,
        )
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)


@app.delete("/admin/domains/{domain}", status_code=204)
def admin_remove_domain(
    domain: str,
    remove_apps: bool = False,
    ignore_dyndns: bool = False,
    dyndns_recovery_password: str | None = None,
    x_admin_token: str = Header(),
) -> Response:
    try:
        admin_connector.remove_domain(
            x_admin_token, domain, remove_apps=remove_apps, ignore_dyndns=ignore_dyndns,
            dyndns_recovery_password=dyndns_recovery_password,
        )
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)


_LOCAL_DOMAIN_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.lan$")


def _check_local_domain_name(domain: str) -> None:
    if not _LOCAL_DOMAIN_RE.match(domain):
        raise HTTPException(
            status_code=400,
            detail={
                "code": "invalid_local_domain",
                "message": f"{domain} n'est pas un domaine .lan a un seul niveau (ex. wappos.lan)",
            },
        )


@app.post("/admin/local-domains", response_model=LocalDomainResult)
def admin_add_local_domain(payload: LocalDomainRequest, x_admin_token: str = Header()) -> LocalDomainResult:
    _check_local_domain_name(payload.domain)
    try:
        admin_connector.add_domain(x_admin_token, payload.domain)
    except WapposApiError as exc:
        _raise_as_http(exc)

    adguard_rewrite_added = None
    if adguard_connector.is_installed():
        try:
            ip = adguard_connector.lan_ip()
            adguard_connector.add_rewrite(payload.domain, ip)
            adguard_rewrite_added = True
        except WapposApiError:
            adguard_rewrite_added = False

    return LocalDomainResult(domain=payload.domain, domain_added=True, adguard_rewrite_added=adguard_rewrite_added)


@app.delete("/admin/local-domains/{domain}", response_model=LocalDomainResult)
def admin_remove_local_domain(domain: str, x_admin_token: str = Header()) -> LocalDomainResult:
    _check_local_domain_name(domain)

    adguard_rewrite_removed = None
    if adguard_connector.is_installed():
        try:
            adguard_connector.remove_rewrite(domain)
            adguard_rewrite_removed = True
        except WapposApiError:
            adguard_rewrite_removed = False

    try:
        admin_connector.remove_domain(x_admin_token, domain)
    except WapposApiError as exc:
        _raise_as_http(exc)

    return LocalDomainResult(domain=domain, domain_added=False, adguard_rewrite_added=adguard_rewrite_removed)


@app.post("/admin/domains/{domain}/dns/push")
def admin_push_domain_dns(
    domain: str, dry_run: bool = True, force: bool = False, purge: bool = False, x_admin_token: str = Header()
) -> dict:
    try:
        return admin_connector.push_domain_dns(x_admin_token, domain, dry_run=dry_run, force=force, purge=purge)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.get("/admin/adguard/status", response_model=AdguardStatus)
def admin_adguard_status(x_admin_token: str = Header()) -> AdguardStatus:
    try:
        admin_connector.list_domain_names(x_admin_token)
        return AdguardStatus(installed=adguard_connector.is_installed())
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.get("/admin/adguard/rewrites", response_model=list[AdguardRewrite])
def admin_adguard_rewrites(x_admin_token: str = Header()) -> list[AdguardRewrite]:
    try:
        admin_connector.list_domain_names(x_admin_token)
        return adguard_connector.list_rewrites()
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.post("/admin/adguard/rewrites", status_code=204)
def admin_adguard_add_rewrite(payload: AdguardRewriteRequest, x_admin_token: str = Header()) -> Response:
    try:
        domains = admin_connector.list_domain_names(x_admin_token, full=True)
        bare_domain = payload.domain[2:] if payload.domain.startswith("*.") else payload.domain
        if bare_domain not in domains and not any(bare_domain.endswith(f".{d}") for d in domains):
            raise UpstreamValidationError(
                f"{payload.domain} n'est pas un domaine enregistre sur ce serveur",
                error_key="adguard_rewrite_unknown_domain",
            )
        adguard_connector.add_rewrite(payload.domain, payload.answer)
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)


@app.delete("/admin/adguard/rewrites/{domain}", status_code=204)
def admin_adguard_remove_rewrite(domain: str, x_admin_token: str = Header()) -> Response:
    try:
        admin_connector.list_domain_names(x_admin_token)
        adguard_connector.remove_rewrite(domain)
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)


@app.get("/admin/apps", response_model=list[AppInfo])
def admin_apps(x_admin_token: str = Header()) -> list[AppInfo]:
    try:
        return admin_connector.list_apps(x_admin_token)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.post("/admin/apps", status_code=200)
def admin_install_app(
    app_id: str = Body(..., embed=True, alias="app"),
    label: str | None = Body(None, embed=True),
    args: str | None = Body(None, embed=True),
    force: bool = Body(False, embed=True),
    x_admin_token: str = Header(),
) -> dict:
    try:
        return admin_connector.install_app(x_admin_token, app_id, label=label, args=args, force=force)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.get("/admin/apps/catalog", response_model=AppCatalog)
def admin_apps_catalog(x_admin_token: str = Header()) -> AppCatalog:
    try:
        return admin_connector.get_app_catalog(x_admin_token)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.get("/admin/apps/manifest", response_model=AppManifest)
def admin_app_manifest(app_id: str, x_admin_token: str = Header()) -> AppManifest:
    try:
        return admin_connector.get_app_manifest(x_admin_token, app_id)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.get("/admin/apps/map")
def admin_app_map(
    app: str | None = None, raw: bool = False, user: str | None = None, x_admin_token: str = Header()
) -> dict:
    try:
        return admin_connector.get_app_map(x_admin_token, app_id=app, raw=raw, user=user)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.get("/admin/apps/{app_id}", response_model=AppDetail)
def admin_app_detail(app_id: str, x_admin_token: str = Header()) -> AppDetail:
    try:
        return admin_connector.get_app_detail(x_admin_token, app_id)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.delete("/admin/apps/{app_id}", status_code=204)
def admin_remove_app(app_id: str, purge: bool = False, x_admin_token: str = Header()) -> Response:
    try:
        admin_connector.remove_app(x_admin_token, app_id, purge=purge)
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)


@app.put("/admin/apps/{app_id}/upgrade")
def admin_upgrade_app(app_id: str, force: bool = False, x_admin_token: str = Header()) -> dict:
    try:
        return admin_connector.upgrade_app(x_admin_token, app_id, force=force)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.put("/admin/apps/{app_id}/changeurl", status_code=204)
def admin_change_app_url(
    app_id: str,
    domain: str = Body(..., embed=True),
    path: str = Body(..., embed=True),
    x_admin_token: str = Header(),
) -> Response:
    try:
        admin_connector.change_app_url(x_admin_token, app_id, domain, path)
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)


@app.put("/admin/apps/{app_id}/label", status_code=204)
def admin_change_app_label(
    app_id: str, new_label: str = Body(..., embed=True), x_admin_token: str = Header()
) -> Response:
    try:
        admin_connector.change_app_label(x_admin_token, app_id, new_label)
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)


@app.put("/admin/apps/{app_id}/dismiss_notification/{name}", status_code=204)
def admin_dismiss_app_notification(app_id: str, name: str, x_admin_token: str = Header()) -> Response:
    try:
        admin_connector.dismiss_app_notification(x_admin_token, app_id, name)
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)


@app.get("/admin/apps/{app_id}/actions")
def admin_app_actions(app_id: str, x_admin_token: str = Header()) -> dict:
    try:
        return admin_connector.list_app_actions(x_admin_token, app_id)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.put("/admin/apps/{app_id}/actions/{action_id}")
def admin_run_app_action(
    app_id: str, action_id: str, args: str | None = Body(None, embed=True), x_admin_token: str = Header()
) -> dict:
    try:
        return admin_connector.run_app_action(x_admin_token, app_id, action_id, args=args)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.get("/admin/apps/{app_id}/config")
def admin_app_config(app_id: str, x_admin_token: str = Header()) -> dict:
    try:
        return admin_connector.get_app_config(x_admin_token, app_id)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.put("/admin/apps/{app_id}/config/{panel_key}")
def admin_set_app_config(
    app_id: str, panel_key: str, args: str = Body(..., embed=True), x_admin_token: str = Header()
) -> dict:
    try:
        return admin_connector.set_app_config(x_admin_token, app_id, panel_key, args)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.get("/admin/permissions", response_model=dict[str, PermissionInfo])
def admin_permissions(x_admin_token: str = Header()) -> dict[str, PermissionInfo]:
    try:
        return admin_connector.list_permissions(x_admin_token)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.put("/admin/permissions/{permission}", status_code=204)
def admin_update_permission(
    permission: str, payload: PermissionUpdateRequest, x_admin_token: str = Header()
) -> Response:
    try:
        admin_connector.update_permission(x_admin_token, permission, add=payload.add, remove=payload.remove)
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)


@app.get("/admin/groups", response_model=list[GroupInfo])
def admin_groups(x_admin_token: str = Header()) -> list[GroupInfo]:
    try:
        return admin_connector.list_groups_full(x_admin_token)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.post("/admin/groups", status_code=204)
def admin_create_group(payload: CreateGroupRequest, x_admin_token: str = Header()) -> Response:
    try:
        admin_connector.create_group(x_admin_token, payload.groupname)
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)


@app.delete("/admin/groups/{groupname}", status_code=204)
def admin_delete_group(groupname: str, x_admin_token: str = Header()) -> Response:
    try:
        admin_connector.delete_group(x_admin_token, groupname)
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)


@app.put("/admin/groups/{groupname}/members", status_code=204)
def admin_update_group_members(
    groupname: str, payload: GroupMembersUpdateRequest, x_admin_token: str = Header()
) -> Response:
    try:
        admin_connector.update_group_members(x_admin_token, groupname, add=payload.add, remove=payload.remove)
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)


@app.get("/admin/groups/{groupname}/aliases", response_model=list[str])
def admin_group_aliases(groupname: str, x_admin_token: str = Header()) -> list[str]:
    try:
        return admin_connector.get_group_mail_aliases(x_admin_token, groupname)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.put("/admin/groups/{groupname}/aliases", status_code=204)
def admin_update_group_aliases(
    groupname: str, payload: GroupAliasesUpdateRequest, x_admin_token: str = Header()
) -> Response:
    try:
        admin_connector.update_group_mailaliases(
            x_admin_token, groupname, add=payload.add, remove=payload.remove, force=payload.force
        )
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)


@app.get("/admin/users/export")
def admin_export_users(x_admin_token: str = Header()) -> Response:
    try:
        csv_text = admin_connector.export_users_csv(x_admin_token)
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=users.csv"},
    )


@app.post("/admin/users/import")
async def admin_import_users(
    csvfile: UploadFile = File(...),
    update: bool = Form(False),
    delete: bool = Form(False),
    x_admin_token: str = Header(),
) -> dict:
    content = await csvfile.read()
    try:
        return admin_connector.import_users_csv(
            x_admin_token, csvfile.filename or "users.csv", content, update=update, delete=delete
        )
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.get("/admin/users/{username}", response_model=UserDetail)
def admin_user_detail(username: str, x_admin_token: str = Header()) -> UserDetail:
    try:
        return admin_connector.get_user(x_admin_token, username)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.put("/admin/permissions/{permission}/properties", status_code=204)
def admin_update_permission_properties(
    permission: str, payload: PermissionPropertiesUpdateRequest, x_admin_token: str = Header()
) -> Response:
    try:
        admin_connector.update_permission_properties(
            x_admin_token, permission, **payload.model_dump(exclude_unset=True)
        )
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)


@app.put("/admin/permissions/{permission}/logo", status_code=204)
async def admin_update_permission_logo(
    permission: str, logo: UploadFile = File(...), x_admin_token: str = Header()
) -> Response:
    content = await logo.read()
    try:
        admin_connector.update_permission_logo(x_admin_token, permission, logo.filename or "logo.png", content)
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)


@app.get("/admin/diagnosis", response_model=list[DiagnosisReport])
def admin_diagnosis(x_admin_token: str = Header()) -> list[DiagnosisReport]:
    try:
        return admin_connector.get_diagnosis(x_admin_token)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.get("/admin/diagnosis/share")
def admin_diagnosis_share(x_admin_token: str = Header()) -> dict:
    try:
        return {"url": admin_connector.share_diagnosis_yunopaste(x_admin_token)}
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.post("/admin/diagnosis/run", response_model=list[DiagnosisReport])
def admin_diagnosis_run(category: str | None = None, x_admin_token: str = Header()) -> list[DiagnosisReport]:
    try:
        admin_connector.run_diagnosis(x_admin_token, category=category)
        return admin_connector.get_diagnosis(x_admin_token)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.put("/admin/diagnosis/{category}/ignore", response_model=list[DiagnosisReport])
def admin_diagnosis_ignore(
    category: str, payload: DiagnosisIgnoreRequest, x_admin_token: str = Header()
) -> list[DiagnosisReport]:
    try:
        admin_connector.ignore_diagnosis_item(x_admin_token, category, payload.meta)
        return admin_connector.get_diagnosis(x_admin_token)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.put("/admin/diagnosis/{category}/unignore", response_model=list[DiagnosisReport])
def admin_diagnosis_unignore(
    category: str, payload: DiagnosisIgnoreRequest, x_admin_token: str = Header()
) -> list[DiagnosisReport]:
    try:
        admin_connector.unignore_diagnosis_item(x_admin_token, category, payload.meta)
        return admin_connector.get_diagnosis(x_admin_token)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.get("/admin/services", response_model=list[ServiceInfo])
def admin_services(x_admin_token: str = Header()) -> list[ServiceInfo]:
    try:
        return admin_connector.list_services(x_admin_token)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.get("/admin/services/{name}", response_model=ServiceInfo)
def admin_service_detail(name: str, x_admin_token: str = Header()) -> ServiceInfo:
    try:
        return admin_connector.get_service(x_admin_token, name)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.put("/admin/services/{name}/start", status_code=204)
def admin_start_service(name: str, x_admin_token: str = Header()) -> Response:
    try:
        admin_connector.start_service(x_admin_token, name)
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)


@app.put("/admin/services/{name}/stop", status_code=204)
def admin_stop_service(name: str, x_admin_token: str = Header()) -> Response:
    try:
        admin_connector.stop_service(x_admin_token, name)
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)


@app.put("/admin/services/{name}/restart", status_code=204)
def admin_restart_service(name: str, x_admin_token: str = Header()) -> Response:
    try:
        admin_connector.restart_service(x_admin_token, name)
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)


@app.put("/admin/services/{name}/enable", status_code=204)
def admin_enable_service(name: str, x_admin_token: str = Header()) -> Response:
    try:
        admin_connector.enable_service(x_admin_token, name)
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)


@app.put("/admin/services/{name}/disable", status_code=204)
def admin_disable_service(name: str, x_admin_token: str = Header()) -> Response:
    try:
        admin_connector.disable_service(x_admin_token, name)
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)


@app.get("/admin/services/{name}/log", response_model=dict[str, list[str]])
def admin_service_log(name: str, number: int = 50, x_admin_token: str = Header()) -> dict[str, list[str]]:
    try:
        return admin_connector.get_service_log(x_admin_token, name, number=number)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.get("/admin/logs", response_model=list[LogEntry])
def admin_logs(limit: int = 50, x_admin_token: str = Header()) -> list[LogEntry]:
    try:
        return admin_connector.list_logs(x_admin_token, limit=limit)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.get("/admin/logs/{name}", response_model=LogDetail)
def admin_log_detail(name: str, number: int = 50, x_admin_token: str = Header()) -> LogDetail:
    try:
        return admin_connector.get_log(x_admin_token, name, number=number)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.get("/admin/logs/{name}/share")
def admin_log_share(name: str, x_admin_token: str = Header()) -> dict[str, str]:
    try:
        return {"url": admin_connector.share_log(x_admin_token, name)}
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.get("/admin/firewall", response_model=FirewallRules)
def admin_firewall(x_admin_token: str = Header()) -> FirewallRules:
    try:
        return admin_connector.list_firewall(x_admin_token)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.put("/admin/firewall/{protocol}/{port}/open", status_code=204)
def admin_open_firewall_port(
    protocol: str, port: str, comment: str = "", upnp: bool = False, x_admin_token: str = Header()
) -> Response:
    try:
        admin_connector.open_firewall_port(x_admin_token, protocol, port, comment=comment, upnp=upnp)
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)


@app.put("/admin/firewall/{protocol}/{port}/close", status_code=204)
def admin_close_firewall_port(
    protocol: str, port: str, upnp_only: bool = False, x_admin_token: str = Header()
) -> Response:
    try:
        admin_connector.close_firewall_port(x_admin_token, protocol, port, upnp_only=upnp_only)
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)


@app.delete("/admin/firewall/{protocol}/{port}", status_code=204)
def admin_delete_firewall_port(protocol: str, port: str, x_admin_token: str = Header()) -> Response:
    try:
        admin_connector.delete_firewall_port(x_admin_token, protocol, port)
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)


@app.put("/admin/firewall/upnp/{enabled}", status_code=204)
def admin_set_upnp(enabled: bool, x_admin_token: str = Header()) -> Response:
    try:
        admin_connector.set_upnp(x_admin_token, enabled)
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)


@app.get("/admin/diagnosis/categories", response_model=list[str])
def admin_diagnosis_categories(x_admin_token: str = Header()) -> list[str]:
    try:
        return admin_connector.list_diagnosis_categories(x_admin_token)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.get("/admin/storage/disks", response_model=list[DiskInfo])
def admin_storage_disks(x_admin_token: str = Header()) -> list[DiskInfo]:
    try:
        return admin_connector.list_disks(x_admin_token)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.get("/admin/storage/mounts", response_model=list[MountInfo])
def admin_storage_mounts(x_admin_token: str = Header()) -> list[MountInfo]:
    try:
        return admin_connector.list_mounts(x_admin_token)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.get("/admin/storage/disks/{name}/smart", response_model=SmartReport)
def admin_storage_disk_smart(name: str, x_admin_token: str = Header()) -> SmartReport:
    try:
        return admin_connector.get_disk_smart(x_admin_token, name)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.get("/admin/system/health", response_model=SystemHealth)
def admin_system_health(x_admin_token: str = Header()) -> SystemHealth:
    try:
        return admin_connector.get_system_health(x_admin_token)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.get("/admin/system/wappos-versions", response_model=list[WapposComponentVersion])
def admin_wappos_versions(x_admin_token: str = Header()) -> list[WapposComponentVersion]:
    try:
        return admin_connector.list_wappos_component_versions(x_admin_token)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.get("/admin/settings")
def admin_get_settings(x_admin_token: str = Header()) -> dict:
    try:
        return admin_connector.get_global_settings(x_admin_token)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.put("/admin/settings/{panel_key}")
def admin_set_settings(panel_key: str, args: str = Body(..., embed=True), x_admin_token: str = Header()) -> dict:
    try:
        return admin_connector.set_global_settings(x_admin_token, panel_key, args)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.delete("/admin/settings/{key}", status_code=204)
def admin_reset_setting(key: str, x_admin_token: str = Header()) -> Response:
    try:
        admin_connector.reset_global_setting(x_admin_token, key)
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)


@app.delete("/admin/settings", status_code=204)
def admin_reset_all_settings(x_admin_token: str = Header()) -> Response:
    try:
        admin_connector.reset_all_global_settings(x_admin_token)
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)


@app.get("/admin/settings/{key}")
def admin_get_setting(key: str, x_admin_token: str = Header()) -> dict:
    try:
        return admin_connector.get_global_setting(x_admin_token, key)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.get("/admin/apps/{app_id}/setting")
def admin_get_app_setting(app_id: str, key: str, x_admin_token: str = Header()) -> dict:
    try:
        return admin_connector.app_setting(x_admin_token, app_id, key)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.put("/admin/apps/{app_id}/setting", status_code=204)
def admin_set_app_setting(
    app_id: str, key: str = Body(...), value: str = Body(...), x_admin_token: str = Header()
) -> Response:
    try:
        admin_connector.app_setting(x_admin_token, app_id, key, value=value)
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)


@app.delete("/admin/apps/{app_id}/setting", status_code=204)
def admin_delete_app_setting(app_id: str, key: str, x_admin_token: str = Header()) -> Response:
    try:
        admin_connector.app_setting(x_admin_token, app_id, key, delete=True)
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)


@app.put("/admin/apps/{app_id}/default", status_code=204)
def admin_app_makedefault(
    app_id: str, domain: str | None = None, undo: bool = False, x_admin_token: str = Header()
) -> Response:
    try:
        admin_connector.app_makedefault(x_admin_token, app_id, domain=domain, undo=undo)
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)


@app.get("/admin/apps/{app_id}/shell")
def admin_app_shell(app_id: str, x_admin_token: str = Header()) -> dict:
    try:
        return {"output": admin_connector.get_app_shell_info(x_admin_token, app_id)}
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.get("/admin/domains/{domain}/urlavailable")
def admin_domain_url_available(domain: str, path: str, x_admin_token: str = Header()) -> dict:
    try:
        return {"available": admin_connector.check_domain_url_available(x_admin_token, domain, path)}
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.put("/admin/domains/{domain}/actions/{action_id}")
def admin_run_domain_action(
    domain: str, action_id: str, args: str | None = Body(None, embed=True), x_admin_token: str = Header()
) -> dict:
    try:
        return admin_connector.run_domain_action(x_admin_token, domain, action_id, args=args)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.put("/admin/firewall/{protocol}/allow/{port}", status_code=204)
def admin_firewall_allow(
    protocol: str,
    port: str,
    ipv4_only: bool = False,
    ipv6_only: bool = False,
    no_upnp: bool = False,
    x_admin_token: str = Header(),
) -> Response:
    try:
        admin_connector.allow_firewall(
            x_admin_token, protocol, port, ipv4_only=ipv4_only, ipv6_only=ipv6_only, no_upnp=no_upnp
        )
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)


@app.put("/admin/firewall/{protocol}/disallow/{port}", status_code=204)
def admin_firewall_disallow(
    protocol: str,
    port: str,
    ipv4_only: bool = False,
    ipv6_only: bool = False,
    upnp_only: bool = False,
    x_admin_token: str = Header(),
) -> Response:
    try:
        admin_connector.disallow_firewall(
            x_admin_token, protocol, port, ipv4_only=ipv4_only, ipv6_only=ipv6_only, upnp_only=upnp_only
        )
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)


@app.get("/admin/storage/disks/{name}")
def admin_disk_info(name: str, x_admin_token: str = Header()) -> dict:
    try:
        return admin_connector.get_disk_info(x_admin_token, name)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.get("/admin/hooks/{action}", response_model=list[str])
def admin_list_hooks(action: str, x_admin_token: str = Header()) -> list[str]:
    try:
        return admin_connector.list_hooks(x_admin_token, action)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.get("/admin/backups")
def admin_list_backups(
    with_info: bool = True, human_readable: bool = False, x_admin_token: str = Header()
) -> dict:
    try:
        return admin_connector.list_backups(x_admin_token, with_info=with_info, human_readable=human_readable)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.post("/admin/backups")
def admin_create_backup(payload: BackupCreateRequest, x_admin_token: str = Header()) -> dict:
    try:
        return admin_connector.create_backup(
            x_admin_token,
            name=payload.name,
            description=payload.description,
            system=payload.system,
            apps=payload.apps,
        )
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.get("/admin/backups/{name}")
def admin_backup_info(
    name: str, with_details: bool = True, human_readable: bool = False, x_admin_token: str = Header()
) -> dict:
    try:
        return admin_connector.get_backup_info(
            x_admin_token, name, with_details=with_details, human_readable=human_readable
        )
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.delete("/admin/backups/{name}", status_code=204)
def admin_delete_backup(name: str, x_admin_token: str = Header()) -> Response:
    try:
        admin_connector.delete_backup(x_admin_token, name)
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)


@app.put("/admin/backups/{name}/restore")
def admin_restore_backup(name: str, payload: BackupRestoreRequest, x_admin_token: str = Header()) -> dict:
    try:
        return admin_connector.restore_backup(
            x_admin_token,
            name,
            system=payload.system,
            apps=payload.apps,
            force=payload.force,
            no_remove_on_failure=payload.no_remove_on_failure,
        )
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.get("/admin/backups/{name}/download")
def admin_download_backup(name: str, x_admin_token: str = Header()) -> StreamingResponse:
    try:
        body, content_type, content_disposition = admin_connector.stream_backup_download(x_admin_token, name)
    except WapposApiError as exc:
        _raise_as_http(exc)
    headers = {"Content-Disposition": content_disposition or f'attachment; filename="{name}.tar.gz"'}
    return StreamingResponse(body, media_type=content_type, headers=headers)


@app.get("/admin/tools/versions")
def admin_versions(x_admin_token: str = Header()) -> dict:
    try:
        return admin_connector.get_versions(x_admin_token)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.get("/admin/tools/update")
def admin_available_updates(x_admin_token: str = Header()) -> dict:
    try:
        return admin_connector.get_available_updates(x_admin_token)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.put("/admin/tools/update/{target}")
def admin_refresh_updates(target: str, no_refresh: bool = False, x_admin_token: str = Header()) -> dict:
    try:
        return admin_connector.refresh_updates(x_admin_token, target=target, no_refresh=no_refresh)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.put("/admin/tools/upgrade/{target}")
def admin_run_upgrade(target: str, x_admin_token: str = Header()) -> dict:
    try:
        return admin_connector.run_upgrade(x_admin_token, target)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.get("/admin/migrations", response_model=list[Migration])
def admin_migrations(pending: bool = False, done: bool = False, x_admin_token: str = Header()) -> list[dict]:
    try:
        return admin_connector.list_migrations(x_admin_token, pending=pending, done=done)
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.put("/admin/migrations")
def admin_run_migrations(payload: MigrationRunRequest, x_admin_token: str = Header()) -> dict:
    try:
        return admin_connector.run_migrations(
            x_admin_token,
            targets=payload.targets or None,
            skip=payload.skip,
            force_rerun=payload.force_rerun,
            accept_disclaimer=payload.accept_disclaimer,
            auto=payload.auto,
        )
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.put("/admin/tools/regenconf")
def admin_regen_conf(payload: RegenConfRequest, x_admin_token: str = Header()) -> dict:
    try:
        return admin_connector.regen_conf(
            x_admin_token,
            names=payload.names,
            with_diff=payload.with_diff,
            force=payload.force,
            dry_run=payload.dry_run,
            list_pending=payload.list_pending,
        )
    except WapposApiError as exc:
        _raise_as_http(exc)


@app.put("/admin/tools/rootpw", status_code=204)
def admin_change_root_password(payload: RootPasswordChangeRequest, x_admin_token: str = Header()) -> Response:
    try:
        admin_connector.change_root_password(x_admin_token, payload.new_password)
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)


@app.put("/admin/tools/reboot", status_code=204)
def admin_reboot(force: bool = False, x_admin_token: str = Header()) -> Response:
    try:
        admin_connector.reboot_server(x_admin_token, force=force)
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)


@app.put("/admin/tools/shutdown", status_code=204)
def admin_shutdown(force: bool = False, x_admin_token: str = Header()) -> Response:
    try:
        admin_connector.shutdown_server(x_admin_token, force=force)
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)


@app.post("/admin/tools/postinstall", status_code=204)
def admin_postinstall(payload: PostinstallRequest, x_admin_token: str = Header()) -> Response:
    try:
        admin_connector.run_postinstall(
            x_admin_token,
            domain=payload.domain,
            username=payload.username,
            fullname=payload.fullname,
            password=payload.password,
            ignore_dyndns=payload.ignore_dyndns,
            force_diskspace=payload.force_diskspace,
            i_have_read_terms_of_services=payload.i_have_read_terms_of_services,
        )
    except WapposApiError as exc:
        _raise_as_http(exc)
    return Response(status_code=204)
