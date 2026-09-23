# Auteur : Patrick Ritaine

from __future__ import annotations

from pydantic import BaseModel


class TlsPassthroughEntry(BaseModel):
    domain: str
    destination: str
    port: int


class TlsPassthroughInfo(BaseModel):
    enabled: bool
    entries: list[TlsPassthroughEntry]


class TlsPassthroughUpdateRequest(BaseModel):
    entries: list[TlsPassthroughEntry]
