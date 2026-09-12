from __future__ import annotations
# Auteur : Patrick Ritaine

from pydantic import BaseModel


class RootPasswordStatus(BaseModel):
    last_changed_date: str | None


class Fail2banStatus(BaseModel):
    available: bool
    jails: dict[str, list[str]]
    total_banned: int


class RootSshKey(BaseModel):
    bits: str
    fingerprint: str
    comment: str
    type: str


class SecurityOverview(BaseModel):
    root_password: RootPasswordStatus
    fail2ban: Fail2banStatus
    root_ssh_keys: list[RootSshKey]
    generated_at: int
