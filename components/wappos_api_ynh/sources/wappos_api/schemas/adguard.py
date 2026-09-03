from __future__ import annotations
# Auteur : Patrick Ritaine

from pydantic import BaseModel


class AdguardStatus(BaseModel):
    installed: bool


class AdguardRewrite(BaseModel):
    domain: str
    answer: str
    enabled: bool


class AdguardRewriteRequest(BaseModel):
    domain: str
    answer: str
