# Auteur : Patrick Ritaine

from __future__ import annotations

from pydantic import BaseModel


class ServiceInfo(BaseModel):
    name: str
    status: str
    start_on_boot: str
    last_state_change: str | float | None = None
    description: str = ""
    configuration: str = "unknown"
    configuration_details: list[str] = []
