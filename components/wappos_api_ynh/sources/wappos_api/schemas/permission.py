# Auteur : Patrick Ritaine

from __future__ import annotations

from pydantic import BaseModel


class PermissionInfo(BaseModel):
    label: str
    url: str | None = None
    allowed: list[str] = []
    description: str | None = None
    order: int | None = None
    show_tile: bool | None = None
    hide_from_public: bool | None = None
    protected: bool | None = None
    logo_hash: str | None = None
    corresponding_users: list[str] = []
    additional_urls: list[str] = []


class PermissionUpdateRequest(BaseModel):
    add: list[str] | None = None
    remove: list[str] | None = None


class PermissionPropertiesUpdateRequest(BaseModel):
    label: str | None = None
    description: str | None = None
    show_tile: bool | None = None
    hide_from_public: bool | None = None
    order: int | None = None
