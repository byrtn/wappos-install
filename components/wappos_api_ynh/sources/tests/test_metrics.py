from __future__ import annotations
# Auteur : Patrick Ritaine

from fastapi.testclient import TestClient

from wappos_api.main import METRICS_TOKEN, app

client = TestClient(app)


def test_metrics_without_token_returns_403() -> None:
    response = client.get("/metrics")
    assert response.status_code == 403


def test_metrics_with_wrong_token_returns_403() -> None:
    response = client.get("/metrics", headers={"Authorization": "Bearer wrong"})
    assert response.status_code == 403


def test_metrics_with_valid_token_returns_prometheus_text() -> None:
    response = client.get("/metrics", headers={"Authorization": f"Bearer {METRICS_TOKEN}"})
    assert response.status_code == 200
    assert b"wappos_api_requests_total" in response.content


def test_metrics_counts_health_requests() -> None:
    client.get("/health")
    response = client.get("/metrics", headers={"Authorization": f"Bearer {METRICS_TOKEN}"})
    assert 'endpoint="/health"' in response.text
