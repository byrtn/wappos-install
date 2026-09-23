# Auteur : Patrick Ritaine

from __future__ import annotations

from pydantic import BaseModel


class DatabaseApp(BaseModel):
    app_id: str
    label: str
    domain: str
    db_name: str


class DatabaseCredentials(BaseModel):
    db_name: str
    db_user: str
    db_pwd: str
