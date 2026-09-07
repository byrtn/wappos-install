# Auteur : Patrick Ritaine
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
    assert b"wappos_admin_requests_total" in resp.data


def test_metrics_endpoint_bypasses_login_gate(client):
    resp = client.get("/metrics", headers={"Authorization": f"Bearer {app.METRICS_TOKEN}"})
    assert resp.status_code == 200


def test_metrics_counts_requests():
    from app import app as flask_app
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        c.get("/app-map")
        resp = c.get("/metrics", headers={"Authorization": f"Bearer {app.METRICS_TOKEN}"})
    body = resp.data.decode()
    assert 'endpoint="app_map_page"' in body
