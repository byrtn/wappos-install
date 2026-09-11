from __future__ import annotations
# Auteur : Patrick Ritaine

from pydantic import BaseModel


class SshAccessStatus(BaseModel):
    password_auth_enabled: bool
