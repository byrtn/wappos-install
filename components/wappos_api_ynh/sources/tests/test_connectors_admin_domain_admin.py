from __future__ import annotations
# Auteur : Patrick Ritaine

import pytest

from wappos_api.connectors import admin
from wappos_api.errors import InvalidCredentialsError, UpstreamUnavailableError


def test_create_and_lookup_domain_admin_session_roundtrip() -> None:
    token = admin._create_domain_admin_session("domain.admin")

    assert token.startswith("da_")
    assert admin._lookup_domain_admin_session(token) == "domain.admin"


def test_domain_admin_sessions_file_is_not_group_or_world_readable() -> None:
    import stat

    admin._create_domain_admin_session("domain.admin")

    mode = admin._domain_admin_sessions_file().stat().st_mode
    assert not (mode & stat.S_IRWXG)
    assert not (mode & stat.S_IRWXO)


def test_lookup_unknown_domain_admin_session_returns_none() -> None:
    assert admin._lookup_domain_admin_session("da_unknown") is None


def test_lookup_expired_domain_admin_session_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    token = admin._create_domain_admin_session("domain.admin")

    real_time = admin.time.time

    def fake_time() -> float:
        return real_time() + admin._DOMAIN_ADMIN_SESSION_VALIDITY + 1

    monkeypatch.setattr(admin.time, "time", fake_time)

    assert admin._lookup_domain_admin_session(token) is None


def test_resolve_upstream_token_passes_through_superadmin_token() -> None:
    assert admin._resolve_upstream_token("abc123") == "abc123"


def test_resolve_upstream_token_rejects_unknown_domain_admin_token() -> None:
    with pytest.raises(InvalidCredentialsError):
        admin._resolve_upstream_token("da_unknown")


def test_resolve_upstream_token_returns_service_session_for_valid_domain_admin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    token = admin._create_domain_admin_session("domain.admin")
    monkeypatch.setattr(admin, "_service_session_token", lambda: "service-token")

    assert admin._resolve_upstream_token(token) == "service-token"


def test_authenticate_domain_admin_rejects_non_member(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(admin, "_ldap_group_members", lambda group: {"someone.else"})

    with pytest.raises(InvalidCredentialsError):
        admin._authenticate_domain_admin("domain.admin", "correct-password")


def test_authenticate_domain_admin_rejects_wrong_password(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(admin, "_ldap_group_members", lambda group: {"domain.admin"})
    monkeypatch.setattr(admin, "_verify_ldap_password", lambda username, password: False)

    with pytest.raises(InvalidCredentialsError):
        admin._authenticate_domain_admin("domain.admin", "wrong-password")


def test_authenticate_domain_admin_accepts_valid_member_on_primary_domain(monkeypatch: pytest.MonkeyPatch) -> None:
    from wappos_api.connectors import domain_owners

    monkeypatch.setattr(admin, "_ldap_group_members", lambda group: {"domain.admin"})
    monkeypatch.setattr(admin, "_verify_ldap_password", lambda username, password: True)
    monkeypatch.setattr(domain_owners, "get_primary_domain", lambda username: "dev.byrtn.fr")

    admin._authenticate_domain_admin("domain.admin", "correct-password", "dev.byrtn.fr")


def test_authenticate_domain_admin_rejects_wrong_login_domain(monkeypatch: pytest.MonkeyPatch) -> None:
    from wappos_api.connectors import domain_owners

    monkeypatch.setattr(admin, "_ldap_group_members", lambda group: {"domain.admin"})
    monkeypatch.setattr(admin, "_verify_ldap_password", lambda username, password: True)
    monkeypatch.setattr(domain_owners, "get_primary_domain", lambda username: "dev.byrtn.fr")

    with pytest.raises(InvalidCredentialsError):
        admin._authenticate_domain_admin("domain.admin", "correct-password", "dev.wappos.fr")


def test_authenticate_domain_admin_rejects_missing_login_domain(monkeypatch: pytest.MonkeyPatch) -> None:
    from wappos_api.connectors import domain_owners

    monkeypatch.setattr(admin, "_ldap_group_members", lambda group: {"domain.admin"})
    monkeypatch.setattr(admin, "_verify_ldap_password", lambda username, password: True)
    monkeypatch.setattr(domain_owners, "get_primary_domain", lambda username: "dev.byrtn.fr")

    with pytest.raises(InvalidCredentialsError):
        admin._authenticate_domain_admin("domain.admin", "correct-password", None)


def test_authenticate_domain_admin_rejects_no_primary_domain_assigned(monkeypatch: pytest.MonkeyPatch) -> None:
    from wappos_api.connectors import domain_owners

    monkeypatch.setattr(admin, "_ldap_group_members", lambda group: {"domain.admin"})
    monkeypatch.setattr(admin, "_verify_ldap_password", lambda username, password: True)
    monkeypatch.setattr(domain_owners, "get_primary_domain", lambda username: None)

    with pytest.raises(InvalidCredentialsError):
        admin._authenticate_domain_admin("domain.admin", "correct-password", "dev.byrtn.fr")


def test_service_session_token_caches_between_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(admin, "_service_session_cache", {})
    monkeypatch.setattr(admin, "_service_account_credentials", lambda: ("wappos_svc_admin", "secret"))
    calls = []

    def fake_login_superadmin(username: str, password: str) -> str:
        calls.append((username, password))
        return "service-session-token"

    monkeypatch.setattr(admin, "_login_superadmin", fake_login_superadmin)

    first = admin._service_session_token()
    second = admin._service_session_token()

    assert first == second == "service-session-token"
    assert len(calls) == 1


def test_service_session_token_refreshes_after_ttl(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(admin, "_service_session_cache", {})
    monkeypatch.setattr(admin, "_service_account_credentials", lambda: ("wappos_svc_admin", "secret"))
    calls = []

    def fake_login_superadmin(username: str, password: str) -> str:
        calls.append((username, password))
        return f"token-{len(calls)}"

    monkeypatch.setattr(admin, "_login_superadmin", fake_login_superadmin)

    first = admin._service_session_token()

    real_time = admin.time.time
    monkeypatch.setattr(admin.time, "time", lambda: real_time() + admin._SERVICE_SESSION_REFRESH_SECONDS + 1)

    second = admin._service_session_token()

    assert first == "token-1"
    assert second == "token-2"
    assert len(calls) == 2


def test_service_account_credentials_missing_file_raises_unavailable(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from wappos_api.config import settings

    monkeypatch.setattr(settings, "wappos_service_account_secret_path", str(tmp_path / "missing.json"))

    with pytest.raises(UpstreamUnavailableError):
        admin._service_account_credentials()
