from __future__ import annotations
# Auteur : Patrick Ritaine

import respx
from fastapi.testclient import TestClient
from httpx import Response

from wappos_api.main import app

client = TestClient(app)


@respx.mock
def test_storage_disks_returns_list(admin_login_url: str) -> None:
    storage_url = admin_login_url.replace("/login", "/storage/disk/list")
    respx.get(storage_url).mock(
        return_value=Response(
            200,
            json={"disks": [{"name": "sda", "model": "Samsung SSD 860", "smartStatus": "SANE", "type": "SSD"}]},
        )
    )

    response = client.get("/admin/storage/disks", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.json()[0]["name"] == "sda"


def test_storage_disks_requires_admin_token() -> None:
    response = client.get("/admin/storage/disks")

    assert response.status_code == 422
