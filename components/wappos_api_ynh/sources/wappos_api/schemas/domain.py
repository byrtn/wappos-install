# Auteur : Patrick Ritaine

from __future__ import annotations

from pydantic import BaseModel


class DomainCertificate(BaseModel):
    CA_type: str = "unknown"
    validity: int = 0
    style: str = "danger"
    summary: str = ""
    ACME_eligible: bool | None = None
    has_wildcards: bool = False


class DomainApp(BaseModel):
    id: str
    name: str
    path: str = ""


class DomainDetail(BaseModel):
    name: str
    certificate: DomainCertificate
    registrar: str = ""
    apps: list[DomainApp] = []
    main: bool = False
    topest_parent: str | None = None


class LocalDomainRequest(BaseModel):
    domain: str


class LocalDomainResult(BaseModel):
    domain: str
    domain_added: bool
    adguard_rewrite_added: bool | None = None
