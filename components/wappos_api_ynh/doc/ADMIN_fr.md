# Wappos API — notes d'administration

Service backend interne, sans utilisateur final direct. Chemin `/wappos-api`
réservé aux administrateurs, pour la supervision et le débogage uniquement
(`GET /wappos-api/health`) — les autres frontends Wappos consomment ce
service en HTTP interne (`127.0.0.1:9400`), jamais via ce chemin public.

## Vérifier que le service tourne

```
systemctl status wappos_api
curl -s http://127.0.0.1:9400/health | python3 -m json.tool
```

Une réponse `"status": "ok"` confirme que les deux connecteurs (portalapi
et l'API REST YunoHost) répondent réellement — pas juste que le service
écoute sur son port.

## Lancer les tests

```
cd /opt/yunohost/wappos_api
venv/bin/pip install -r requirements-dev.txt
venv/bin/python3 -m pytest
```

Les tests ne dépendent jamais d'une vraie instance YunoHost — l'API est
simulée (respx). La vérification en conditions réelles se fait séparément,
à la main, documentée dans le CDC (section 2) et le journal du 05/08/2026.
