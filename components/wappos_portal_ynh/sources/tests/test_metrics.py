# Auteur : Patrick Ritaine
from unittest.mock import patch

import app


def test_metrics_without_token_returns_403(client):
    resp = client.get("/metrics")
    assert resp.status_code == 403


def test_metrics_with_wrong_token_returns_403(client):
    resp = client.get("/metrics", headers={"Authorization": "Bearer wrong"})
    assert resp.status_code == 403


def test_metrics_with_valid_token_returns_prometheus_text(client):
    resp = client.get("/metrics", headers={"Authorization": f"Bearer {app.METRICS_TOKEN}"})
    assert resp.status_code == 200
    assert b"wappos_portal_requests_total" in resp.data


def test_metrics_does_not_trigger_branding_fetch(client):
    with patch.object(app, "_public_settings_safe") as mocked:
        resp = client.get("/metrics", headers={"Authorization": f"Bearer {app.METRICS_TOKEN}"})
    assert resp.status_code == 200
    mocked.assert_not_called()
