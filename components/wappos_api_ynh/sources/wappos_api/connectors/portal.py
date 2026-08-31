# Auteur : Patrick Ritaine

from __future__ import annotations

import http.cookies

import httpx

from wappos_api.config import settings
from wappos_api.errors import (
    InvalidCredentialsError,
    UpstreamProtocolError,
    UpstreamUnavailableError,
    UpstreamValidationError,
)


def _host_header(host: str) -> dict[str, str]:
    return {"Host": host, "locale": "fr"}


def _extract_portal_cookie(response: httpx.Response) -> str | None:
    for raw_cookie in response.headers.get_list("set-cookie"):
        jar: http.cookies.SimpleCookie = http.cookies.SimpleCookie()
        jar.load(raw_cookie)
        if "yunohost.portal" in jar:
            return jar["yunohost.portal"].value
    return None


def _extract_portal_cookie_header(response: httpx.Response) -> str | None:
    for raw_cookie in response.headers.get_list("set-cookie"):
        if raw_cookie.split("=", 1)[0].strip() == "yunohost.portal":
            return raw_cookie
    return None


def login(host: str, user: str, password: str) -> tuple[str, str | None]:
    try:
        response = httpx.post(
            f"{settings.portalapi_base_url}/login",
            json={"credentials": f"{user}:{password}"},
            headers=_host_header(host),
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("portalapi login unreachable") from exc

    if response.status_code == 401:
        raise InvalidCredentialsError("portalapi rejected the given credentials")
    if response.status_code >= 400:
        raise UpstreamProtocolError(f"portalapi login returned unexpected status {response.status_code}")

    token = _extract_portal_cookie(response)
    if not token:
        raise UpstreamProtocolError("portalapi login succeeded but returned no session cookie")
    return token, _extract_portal_cookie_header(response)


def logout(host: str, token: str) -> str | None:
    try:
        response = httpx.get(
            f"{settings.portalapi_base_url}/logout",
            headers=_host_header(host),
            cookies={"yunohost.portal": token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("portalapi logout unreachable") from exc

    if response.status_code >= 400 and response.status_code != 401:
        raise UpstreamProtocolError(f"portalapi logout returned unexpected status {response.status_code}")
    return _extract_portal_cookie_header(response)


def me(host: str, token: str) -> dict:
    try:
        response = httpx.get(
            f"{settings.portalapi_base_url}/me",
            headers=_host_header(host),
            cookies={"yunohost.portal": token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("portalapi /me unreachable") from exc

    if response.status_code == 401:
        raise InvalidCredentialsError("portalapi session token rejected")
    if response.status_code >= 400:
        raise UpstreamProtocolError(f"portalapi /me returned unexpected status {response.status_code}")
    return response.json()


def update(host: str, token: str, **fields: object) -> None:
    try:
        response = httpx.put(
            f"{settings.portalapi_base_url}/update",
            json=fields,
            headers=_host_header(host),
            cookies={"yunohost.portal": token},
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("portalapi /update unreachable") from exc

    if response.status_code == 401:
        raise InvalidCredentialsError("portalapi session token rejected")
    if response.status_code >= 400:
        error_key = None
        try:
            error_key = response.json().get("error_key")
        except ValueError:
            pass
        if error_key:
            raise UpstreamValidationError(
                f"portalapi /update rejected: {error_key}", error_key=error_key
            )
        raise UpstreamProtocolError(f"portalapi /update returned unexpected status {response.status_code}")


def ping(host: str) -> None:
    public(host)


def public(host: str, token: str | None = None) -> dict:
    try:
        response = httpx.get(
            f"{settings.portalapi_base_url}/public",
            headers=_host_header(host),
            cookies={"yunohost.portal": token} if token else None,
            timeout=settings.upstream_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise UpstreamUnavailableError("portalapi /public unreachable") from exc

    if response.status_code >= 400:
        raise UpstreamProtocolError(f"portalapi /public returned unexpected status {response.status_code}")
    return response.json()
