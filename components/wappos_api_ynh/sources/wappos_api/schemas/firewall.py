# Auteur : Patrick Ritaine

from __future__ import annotations

from pydantic import BaseModel


class FirewallPort(BaseModel):
    port: int | str
    open: bool
    upnp: bool
    comment: str = ""


class FirewallRules(BaseModel):
    tcp: list[FirewallPort] = []
    udp: list[FirewallPort] = []
    upnp_enabled: bool = False
