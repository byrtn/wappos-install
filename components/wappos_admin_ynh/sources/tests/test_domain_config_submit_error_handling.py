# Auteur : Patrick Ritaine
from unittest.mock import patch

import requests

import app


_CONFIG = {
    "panels": [
        {
            "id": "feature",
            "sections": [
                {"id": "main", "options": [{"id": "mail_in", "type": "boolean"}]},
            ],
        },
    ],
}


def test_domain_config_submit_shows_generic_error_on_timeout(logged_in_client):
    with patch.object(app, "_wappos_api_domain_config", return_value=_CONFIG), \
         patch.object(
             app, "_wappos_api_set_domain_config",
             side_effect=requests.exceptions.ReadTimeout("timed out"),
         ):
        resp = logged_in_client.post(
            "/domains/dev.byrtn.fr/config/feature",
            data={"__section_id__": "main", "mail_in": "1"},
        )
    assert resp.status_code == 302
    assert "error=" in resp.headers["Location"]


def test_domain_config_submit_succeeds_when_upstream_ok(logged_in_client):
    with patch.object(app, "_wappos_api_domain_config", return_value=_CONFIG), \
         patch.object(app, "_wappos_api_set_domain_config") as mocked_set:
        resp = logged_in_client.post(
            "/domains/dev.byrtn.fr/config/feature",
            data={"__section_id__": "main", "mail_in": "1"},
        )
    assert resp.status_code == 302
    assert "msg=" in resp.headers["Location"]
    mocked_set.assert_called_once()
