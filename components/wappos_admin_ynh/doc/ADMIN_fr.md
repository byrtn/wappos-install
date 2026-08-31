# Wappos Admin — notes d'administration

MVP du portail d'administration Wappos (Phase 2, premier vrai client du
connecteur Admin de `wappos_api`). Couvre actuellement une seule
fonctionnalité : liste des utilisateurs en lecture seule. Permission
admin-only — protégée par SSOwat comme n'importe quelle app YunoHost, pas
de page de connexion propre.

## Vérifier que le service tourne

```
systemctl status wappos_admin
curl -s http://127.0.0.1:9500/ -H "Authorization: Basic ..."
```

## Dépend de

`wappos_api` doit être installée et démarrée (`127.0.0.1:9400`) — cette app
ne parle jamais directement à YunoHost, uniquement via les routes du
connecteur Admin (`/admin/login`, `/admin/users`).
