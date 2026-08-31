# Wappos Admin — admin notes

MVP of the Wappos administration portal (Phase 2, first real client of
`wappos_api`'s Admin connector). Currently covers a single feature:
read-only user list. Admin-only permission — protected by SSOwat like any
other YunoHost app, no login page of its own.

## Check the service is running

```
systemctl status wappos_admin
curl -s http://127.0.0.1:9500/ -H "Authorization: Basic ..." 
```

## Depends on

`wappos_api` must be installed and running (`127.0.0.1:9400`) — this app
never talks to YunoHost directly, only through the Admin connector routes
(`/admin/login`, `/admin/users`).
