# Auteur : Patrick Ritaine

from __future__ import annotations

from pydantic import BaseModel


class AdminLoginRequest(BaseModel):
    user: str
    password: str


class AdminTokenResponse(BaseModel):
    token: str


class CreateUserRequest(BaseModel):
    username: str
    domain: str
    password: str
    fullname: str
    mailbox_quota: str = "0"


class UpdateUserRequest(BaseModel):
    mail: str | None = None
    change_password: str | None = None
    add_mailforward: list[str] | None = None
    remove_mailforward: list[str] | None = None
    add_mailalias: list[str] | None = None
    remove_mailalias: list[str] | None = None
    mailbox_quota: str | None = None
    fullname: str | None = None
