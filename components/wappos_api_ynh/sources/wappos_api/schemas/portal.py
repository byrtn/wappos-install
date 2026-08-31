# Auteur : Patrick Ritaine

from __future__ import annotations

from pydantic import BaseModel


class PortalLoginRequest(BaseModel):
    user: str
    password: str


class PortalTokenResponse(BaseModel):
    token: str
    cookie: str | None = None


class PortalLogoutResponse(BaseModel):
    cookie: str | None = None
