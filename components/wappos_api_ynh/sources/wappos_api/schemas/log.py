# Auteur : Patrick Ritaine

from __future__ import annotations

from pydantic import BaseModel


class LogEntry(BaseModel):
    name: str
    description: str
    success: bool | str = "?"
    started_at: str | None = None


class LogSuboperation(BaseModel):
    name: str
    description: str
    success: bool | str = "?"


class LogDetail(BaseModel):
    name: str
    description: str
    path: str | None = None
    started_at: str | None = None
    ended_at: str | None = None
    error: bool = False
    suboperations: list[LogSuboperation] = []
    logs: list[str] = []
    more_logs_available: bool = False
