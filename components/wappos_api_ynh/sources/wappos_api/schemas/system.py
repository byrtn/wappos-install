from __future__ import annotations
# Auteur : Patrick Ritaine

from pydantic import BaseModel


class WapposComponentVersion(BaseModel):
    id: str
    name: str
    version: str


class SystemHealth(BaseModel):
    hostname: str
    os_name: str
    kernel: str
    cpu_count: int
    load_1min: float
    load_5min: float
    load_15min: float
    uptime_seconds: int
    uptime_human: str
    reboot_required: bool
    ram_total_bytes: int
    ram_used_bytes: int
    ram_available_bytes: int
    ram_used_percent: float
    ram_total_human: str
    ram_used_human: str
    ram_available_human: str
    swap_total_bytes: int
    swap_used_bytes: int
    swap_used_percent: float
    swap_total_human: str
    swap_used_human: str
