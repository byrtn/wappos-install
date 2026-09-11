# Auteur : Patrick Ritaine
from unittest.mock import patch

import app


def _patch_domain_detail_deps(**overrides):
    defaults = {
        "_wappos_api_domain_detail": {
            "name": "dev.byrtn.fr", "registrar": None, "main": False, "apps": [],
            "certificate": {"style": "success", "CA_type": "letsencrypt", "validity": 80},
        },
        "_wappos_api_domain_config": {"panels": [{"id": "dns", "sections": []}]},
        "_wappos_api_domain_dns_suggest": "",
        "_wappos_api_settings": {"panels": []},
    }
    defaults.update(overrides)
    return [patch.object(app, name, return_value=value) for name, value in defaults.items()]


def test_domain_detail_does_not_call_dns_push_by_default(logged_in_client):
    patches = _patch_domain_detail_deps()
    for p in patches:
        p.start()
    try:
        with patch.object(app, "_wappos_api_push_domain_dns") as mocked_push:
            resp = logged_in_client.get("/domains/dev.byrtn.fr")
    finally:
        for p in patches:
            p.stop()
    assert resp.status_code == 200
    mocked_push.assert_not_called()
    assert "Check DNS synchronization" in resp.data.decode()


def test_domain_detail_calls_dns_push_when_check_requested(logged_in_client):
    patches = _patch_domain_detail_deps()
    for p in patches:
        p.start()
    try:
        with patch.object(app, "_wappos_api_push_domain_dns", return_value={"create": [], "update": [], "delete": [], "unchanged": []}) as mocked_push:
            resp = logged_in_client.get("/domains/dev.byrtn.fr?check_dns_push=1")
    finally:
        for p in patches:
            p.stop()
    assert resp.status_code == 200
    mocked_push.assert_called_once_with("test-token", "dev.byrtn.fr", dry_run=True)
    assert "already synchronized" in resp.data.decode()
