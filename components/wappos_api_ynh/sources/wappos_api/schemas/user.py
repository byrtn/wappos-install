# Auteur : Patrick Ritaine

from __future__ import annotations

from pydantic import BaseModel


class User(BaseModel):
    username: str
    fullname: str
    mail: str


class UserDetail(BaseModel):
    username: str
    fullname: str
    mail: str
    mail_aliases: list[str] = []
    mail_forward: list[str] = []
    mailbox_quota_limit: str = "0"
    mailbox_quota_use: str = "?"


class SshKey(BaseModel):
    key: str
    name: str = ""


class SshKeyAddRequest(BaseModel):
    key: str
    comment: str | None = None


class SshKeyRemoveRequest(BaseModel):
    key: str
