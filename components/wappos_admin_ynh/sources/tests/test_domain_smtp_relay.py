# Auteur : Patrick Ritaine
from unittest.mock import patch

import app


def test_domain_smtp_relay_set_requires_host_and_port(logged_in_client):
    resp = logged_in_client.post("/domains/dev.byrtn.fr/smtp-relay/set", data={"host": "", "port": ""})
    assert resp.status_code == 302
    assert "error=" in resp.headers["Location"]


def test_domain_smtp_relay_set_calls_api(logged_in_client):
    with patch.object(app, "_wappos_api_set_domain_smtp_relay") as set_mock:
        resp = logged_in_client.post(
            "/domains/dev.byrtn.fr/smtp-relay/set",
            data={"host": "smtp.example.com", "port": "587", "user": "u", "password": "p"},
        )
    assert resp.status_code == 302
    assert "error=" not in resp.headers["Location"]
    set_mock.assert_called_once_with("test-token", "dev.byrtn.fr", "smtp.example.com", 587, "u", "p")


def test_domain_smtp_relay_remove_calls_api(logged_in_client):
    with patch.object(app, "_wappos_api_remove_domain_smtp_relay") as remove_mock:
        resp = logged_in_client.post("/domains/dev.byrtn.fr/smtp-relay/remove")
    assert resp.status_code == 302
    remove_mock.assert_called_once_with("test-token", "dev.byrtn.fr")
