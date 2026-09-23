from __future__ import annotations
# Auteur : Patrick Ritaine

import pytest

from wappos_api.config import settings
from wappos_api.connectors import domain_owners
from wappos_api.errors import UpstreamValidationError


@pytest.fixture(autouse=True)
def _isolate_registry(tmp_path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "wappos_domain_owners_path", str(tmp_path / "wappos_domain_owners.json"))
    monkeypatch.setattr(settings, "wappos_domain_admin_primary_path", str(tmp_path / "wappos_domain_admin_primary.json"))


def test_list_owners_empty_when_no_registry_file() -> None:
    assert domain_owners.list_owners() == {}


def test_set_and_get_owners_roundtrip() -> None:
    domain_owners.set_owners("dev.byrtn.fr", ["patrick", "amelle"])

    assert domain_owners.get_owners("dev.byrtn.fr") == ["amelle", "patrick"]
    assert domain_owners.list_owners() == {"dev.byrtn.fr": ["amelle", "patrick"]}


def test_set_owners_with_empty_list_removes_domain() -> None:
    domain_owners.set_owners("dev.byrtn.fr", ["patrick"])
    domain_owners.set_owners("dev.byrtn.fr", [])

    assert domain_owners.get_owners("dev.byrtn.fr") == []
    assert "dev.byrtn.fr" not in domain_owners.list_owners()


def test_add_owner_deduplicates() -> None:
    domain_owners.add_owner("dev.byrtn.fr", "patrick")
    domain_owners.add_owner("dev.byrtn.fr", "patrick")
    domain_owners.add_owner("dev.byrtn.fr", "amelle")

    assert domain_owners.get_owners("dev.byrtn.fr") == ["amelle", "patrick"]


def test_remove_owner_removes_domain_when_last_owner_removed() -> None:
    domain_owners.add_owner("dev.byrtn.fr", "patrick")
    domain_owners.remove_owner("dev.byrtn.fr", "patrick")

    assert domain_owners.get_owners("dev.byrtn.fr") == []
    assert "dev.byrtn.fr" not in domain_owners.list_owners()


def test_domains_owned_by_returns_only_matching_domains() -> None:
    domain_owners.set_owners("dev.byrtn.fr", ["patrick"])
    domain_owners.set_owners("dev.wappos.fr", ["amelle"])

    assert domain_owners.domains_owned_by("patrick") == ["dev.byrtn.fr"]


def test_find_parent_domain_returns_closest_match() -> None:
    domain_owners.set_owners("byrtn.fr", ["patrick"])
    domain_owners.set_owners("dev.byrtn.fr", ["patrick"])

    assert domain_owners.find_parent_domain("photography.dev.byrtn.fr") == "dev.byrtn.fr"


def test_find_parent_domain_returns_none_when_no_match() -> None:
    domain_owners.set_owners("dev.byrtn.fr", ["patrick"])

    assert domain_owners.find_parent_domain("dev.wappos.fr") is None


def test_inherit_ownership_for_new_domain_copies_parent_owners() -> None:
    domain_owners.set_owners("dev.byrtn.fr", ["patrick"])

    inherited = domain_owners.inherit_ownership_for_new_domain("photography.dev.byrtn.fr")

    assert inherited == ["patrick"]
    assert domain_owners.get_owners("photography.dev.byrtn.fr") == ["patrick"]


def test_inherit_ownership_for_new_domain_returns_empty_without_owned_parent() -> None:
    inherited = domain_owners.inherit_ownership_for_new_domain("dev.byrtn.fr")

    assert inherited == []
    assert "dev.byrtn.fr" not in domain_owners.list_owners()


def test_require_known_domain_format_rejects_path_traversal() -> None:
    with pytest.raises(UpstreamValidationError):
        domain_owners.require_known_domain_format("../etc/passwd")


def test_require_known_domain_format_accepts_normal_domain() -> None:
    domain_owners.require_known_domain_format("dev.byrtn.fr")


def test_get_primary_domain_returns_none_when_unset() -> None:
    assert domain_owners.get_primary_domain("patrick") is None


def test_set_and_get_primary_domain_roundtrip() -> None:
    domain_owners.set_owners("dev.byrtn.fr", ["patrick"])
    domain_owners.set_primary_domain("patrick", "dev.byrtn.fr")

    assert domain_owners.get_primary_domain("patrick") == "dev.byrtn.fr"


def test_set_primary_domain_rejects_domain_not_owned() -> None:
    with pytest.raises(UpstreamValidationError):
        domain_owners.set_primary_domain("patrick", "dev.byrtn.fr")


def test_set_owners_clears_primary_domain_when_owner_removed() -> None:
    domain_owners.set_owners("dev.byrtn.fr", ["patrick"])
    domain_owners.set_primary_domain("patrick", "dev.byrtn.fr")

    domain_owners.set_owners("dev.byrtn.fr", [])

    assert domain_owners.get_primary_domain("patrick") is None


def test_set_owners_keeps_primary_domain_when_owner_stays() -> None:
    domain_owners.set_owners("dev.byrtn.fr", ["patrick", "amelle"])
    domain_owners.set_primary_domain("patrick", "dev.byrtn.fr")

    domain_owners.set_owners("dev.byrtn.fr", ["patrick"])

    assert domain_owners.get_primary_domain("patrick") == "dev.byrtn.fr"


def test_remove_owner_clears_primary_domain() -> None:
    domain_owners.set_owners("dev.byrtn.fr", ["patrick"])
    domain_owners.set_primary_domain("patrick", "dev.byrtn.fr")

    domain_owners.remove_owner("dev.byrtn.fr", "patrick")

    assert domain_owners.get_primary_domain("patrick") is None
