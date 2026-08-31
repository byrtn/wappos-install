# Auteur : Patrick Ritaine

from __future__ import annotations

from pydantic import BaseModel


class DiagnosisItem(BaseModel):
    status: str
    summary: str
    details: list[str] = []
    meta: dict = {}
    ignored: bool = False


class DiagnosisReport(BaseModel):
    id: str
    description: str
    status: str
    items: list[DiagnosisItem]
    last_execution: float | None = None
    error_count: int = 0
    warning_count: int = 0
    ignored_count: int = 0


class DiagnosisIgnoreRequest(BaseModel):
    meta: dict = {}
