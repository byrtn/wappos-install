# Auteur : Patrick Ritaine

from __future__ import annotations

from pydantic import BaseModel


class GroupInfo(BaseModel):
    name: str
    members: list[str] = []
    permissions: list[str] = []
    is_special: bool = False


class CreateGroupRequest(BaseModel):
    groupname: str


class GroupMembersUpdateRequest(BaseModel):
    add: list[str] | None = None
    remove: list[str] | None = None


class GroupAliasesUpdateRequest(BaseModel):
    add: list[str] | None = None
    remove: list[str] | None = None
    force: bool = False
