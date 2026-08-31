from __future__ import annotations
# Auteur : Patrick Ritaine

from pydantic import BaseModel


class RegenConfRequest(BaseModel):
    names: list[str] | None = None
    with_diff: bool = False
    force: bool = False
    dry_run: bool = False
    list_pending: bool = False


class RootPasswordChangeRequest(BaseModel):
    new_password: str


class PostinstallRequest(BaseModel):
    domain: str
    username: str
    fullname: str
    password: str
    ignore_dyndns: bool = False
    force_diskspace: bool = False
    i_have_read_terms_of_services: bool = False
