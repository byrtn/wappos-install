# Auteur : Patrick Ritaine

from __future__ import annotations

from pydantic import BaseModel


class DomainSmtpRelay(BaseModel):
    host: str
    port: int
    user: str
    has_password: bool


class DomainSmtpRelayRequest(BaseModel):
    host: str
    port: int
    user: str = ""
    password: str = ""
