# Wappos API — admin notes

Internal backend service, no direct end user. `/wappos-api` is admin-only,
reserved for supervision/debugging only (`GET /wappos-api/health`) — other
Wappos frontends consume this service over internal HTTP
(`127.0.0.1:9400`), never through this public path.

## Check the service is running

```
systemctl status wappos_api
curl -s http://127.0.0.1:9400/health | python3 -m json.tool
```

A `"status": "ok"` response confirms both connectors (portalapi and the
YunoHost REST API) actually respond — not just that the service is
listening.

## Run the tests

```
cd /opt/yunohost/wappos_api
venv/bin/pip install -r requirements-dev.txt
venv/bin/python3 -m pytest
```

Tests never depend on a real YunoHost instance — the API is simulated
(respx). Real-conditions verification is done separately, by hand,
documented in the CDC (section 2) and the 2026-08-05 journal.
