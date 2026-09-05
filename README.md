# wappos-install

Installeur Wappos (YunoHost + composants Wappos). Deux façons d'installer, au choix.

## Méthode 1 — Depuis l'ISO (bare metal ou n'importe quel hyperviseur)

Construisez l'ISO à partir de `build-iso.sh` (nécessite une ISO Debian 12 netinst en entrée) et démarrez dessus. Répondez aux questions Debian standards (langue, clavier, fuseau horaire, partitionnement, nom de machine, réseau, mot de passe root) — le reste s'installe automatiquement, y compris Wappos, jusqu'à l'affichage des identifiants de connexion.

À la fin de l'installation Debian, la machine s'éteint toute seule. Redémarrez-la — Wappos s'installe alors tout seul, sans autre intervention.

## Méthode 2 — Sur un Debian 12 déjà installé

```bash
git clone https://github.com/byrtn/wappos-install.git
cd wappos-install
./install-wappos.sh
```

À exécuter en tant que root. Le script installe le socle système, Docker, les composants Wappos, et affiche à la fin l'adresse et les identifiants de connexion.
