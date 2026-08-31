# Auteur : Patrick Ritaine

from __future__ import annotations

from pydantic import BaseModel


class AppInfo(BaseModel):
    id: str
    name: str
    description: str
    version: str
    domain_path: str | None = None
    logo: str | None = None


class AppUpgradeInfo(BaseModel):
    status: str
    message: str
    current_version: str
    new_version: str | None = None
    pre_upgrade_notifications: dict[str, str] = {}
    specific_channel: str | None = None
    specific_channel_message: str | None = None


class AppDetail(BaseModel):
    id: str
    label: str
    version: str
    description: str = ""
    domain_path: str | None = None
    logo: str | None = None
    is_webapp: bool = False
    supports_change_url: bool = False
    supports_purge: bool = False
    supports_config_panel: bool = False
    upgrade: AppUpgradeInfo
    notification_post_install: str | None = None
    notifications_post_upgrade: dict[str, str] = {}


class AppCatalogEntry(BaseModel):
    id: str
    name: str
    description: str = ""
    level: int | str = -1
    installed: bool = False
    logo_hash: str | None = None
    category: str | None = None
    subtags: list[str] = []
    maintained: bool = True
    state: str = "working"
    multi_instance: bool = False
    antifeatures: list[str] = []
    potential_alternative_to: list[str] = []


class AppCatalogSubtag(BaseModel):
    id: str
    title: str


class AppCatalogCategory(BaseModel):
    id: str
    title: str
    description: str = ""
    icon: str = ""
    subtags: list[AppCatalogSubtag] = []


class AppCatalogAntifeature(BaseModel):
    id: str
    title: str = ""
    description: str = ""


class AppCatalog(BaseModel):
    apps: list[AppCatalogEntry]
    categories: list[AppCatalogCategory] = []
    antifeatures: list[AppCatalogAntifeature] = []


class AppUpstreamInfo(BaseModel):
    license: str | None = None
    website: str | None = None
    admindoc: str | None = None
    userdoc: str | None = None
    code: str | None = None


class AppManifest(BaseModel):
    id: str
    name: str
    description: str = ""
    version: str = ""
    install: list[dict] = []
    upstream: AppUpstreamInfo = AppUpstreamInfo()
    requirements: dict[str, dict] = {}
