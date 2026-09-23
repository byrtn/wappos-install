# Auteur : Patrick Ritaine

from __future__ import annotations

from pydantic import BaseModel


class DomainOwnersResponse(BaseModel):
    domain: str
    owners: list[str]


class DomainOwnersUpdateRequest(BaseModel):
    owners: list[str]


class PrimaryDomainResponse(BaseModel):
    username: str
    domain: str | None


class PrimaryDomainUpdateRequest(BaseModel):
    domain: str
