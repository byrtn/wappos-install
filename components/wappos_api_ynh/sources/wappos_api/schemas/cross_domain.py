from __future__ import annotations
# Auteur : Patrick Ritaine

from pydantic import BaseModel


class CrossDomainStatus(BaseModel):
    enabled: bool
