from __future__ import annotations
# Auteur : Patrick Ritaine

import pytest
import respx
from httpx import Response

from wappos_api.connectors import admin
from wappos_api.errors import InvalidCredentialsError, UpstreamProtocolError


@pytest.fixture
def admin_diagnosis_categories_url(admin_login_url: str) -> str:
    return admin_login_url.replace("/login", "/diagnosis/categories")


@respx.mock
def test_list_diagnosis_categories_parses_real_shape(admin_diagnosis_categories_url: str) -> None:
    respx.get(admin_diagnosis_categories_url).mock(
        return_value=Response(200, json={"categories": ["ip", "dnsrecords", "mail", "web"]})
    )

    categories = admin.list_diagnosis_categories("fake-session-token")

    assert categories == ["ip", "dnsrecords", "mail", "web"]


@respx.mock
def test_list_diagnosis_categories_rejects_invalid_session(admin_diagnosis_categories_url: str) -> None:
    respx.get(admin_diagnosis_categories_url).mock(return_value=Response(401))

    with pytest.raises(InvalidCredentialsError):
        admin.list_diagnosis_categories("expired-token")


@respx.mock
def test_list_diagnosis_categories_unexpected_shape_raises_protocol_error(
    admin_diagnosis_categories_url: str,
) -> None:
    respx.get(admin_diagnosis_categories_url).mock(return_value=Response(200, json={"unexpected": "shape"}))

    with pytest.raises(UpstreamProtocolError):
        admin.list_diagnosis_categories("fake-session-token")
