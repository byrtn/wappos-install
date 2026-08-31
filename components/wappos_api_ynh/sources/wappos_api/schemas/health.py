from __future__ import annotations
# Auteur : Patrick Ritaine

from typing import Literal

from pydantic import BaseModel

ConnectorStatus = Literal["ok", "unreachable"]


class ConnectorHealth(BaseModel):
    status: ConnectorStatus
    detail: str | None = None


class HealthReport(BaseModel):
    status: Literal["ok", "degraded"]
    portalapi: ConnectorHealth
    yunohost_api: ConnectorHealth
