# Auteur : Patrick Ritaine

from __future__ import annotations

from pydantic import BaseModel


class DiskInfo(BaseModel):
    name: str
    model: str = ""
    serial: str = ""
    removable: bool = False
    size: str | int = ""
    smart_status: str = "UNKNOWN"
    connection_bus: str | None = None
    type: str = ""
    rpm: str | int | None = None


class MountConsumer(BaseModel):
    path: str
    label: str
    size_bytes: int
    size_human: str


class MountInfo(BaseModel):
    mountpoint: str
    label: str
    device: str
    fstype: str
    total_bytes: int
    used_bytes: int
    free_bytes: int
    used_percent: float
    total_human: str
    used_human: str
    free_human: str
    top_consumers: list[MountConsumer] = []


class SmartAttribute(BaseModel):
    id: int
    name: str
    value: int
    worst: int
    threshold: int
    raw_value: str
    when_failed: str = ""


class SmartReport(BaseModel):
    name: str
    available: bool
    unavailable_reason: str = ""
    passed: bool | None = None
    temperature_celsius: int | None = None
    power_on_hours: int | None = None
    power_cycle_count: int | None = None
    attributes: list[SmartAttribute] = []
    nvme_percentage_used: int | None = None
    nvme_media_errors: int | None = None
    nvme_unsafe_shutdowns: int | None = None
    nvme_data_units_read: int | None = None
    nvme_data_units_written: int | None = None
