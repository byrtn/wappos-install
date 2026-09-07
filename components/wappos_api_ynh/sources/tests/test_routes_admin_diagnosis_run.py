from __future__ import annotations
# Auteur : Patrick Ritaine

import respx
from fastapi.testclient import TestClient
from httpx import Response

from wappos_api.main import app

client = TestClient(app)


@respx.mock
def test_diagnosis_run_returns_fresh_reports(admin_login_url: str) -> None:
    run_url = admin_login_url.replace("/login", "/diagnosis/run")
    diagnosis_url = admin_login_url.replace("/login", "/diagnosis")
    respx.put(run_url).mock(return_value=Response(200))
    respx.get(diagnosis_url).mock(
        return_value=Response(
            200,
            json={"reports": [{"id": "ip", "description": "IP", "items": [{"status": "SUCCESS", "summary": "ok"}]}]},
        )
    )

    response = client.post("/admin/diagnosis/run", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.json()[0]["status"] == "SUCCESS"


@respx.mock
def test_diagnosis_run_rejects_invalid_session(admin_login_url: str) -> None:
    run_url = admin_login_url.replace("/login", "/diagnosis/run")
    respx.put(run_url).mock(return_value=Response(401))

    response = client.post("/admin/diagnosis/run", headers={"X-Admin-Token": "expired-token"})

    assert response.status_code == 401
