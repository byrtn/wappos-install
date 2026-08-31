from __future__ import annotations
# Auteur : Patrick Ritaine

from pydantic import BaseModel


class BackupCreateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    system: list[str] | None = None
    apps: list[str] | None = None


class BackupRestoreRequest(BaseModel):
    system: list[str] | None = None
    apps: list[str] | None = None
    force: bool = False
    no_remove_on_failure: bool = False
