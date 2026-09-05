# wappos-install

Installeur Wappos (YunoHost + composants Wappos). Deux façons d'installer, au choix.

## Méthode 1 — Depuis l'ISO (bare metal ou n'importe quel hyperviseur)

Téléchargez l'ISO déjà construite, prête à l'emploi :

**[Télécharger l'ISO Wappos](https://github.com/byrtn/wappos-install/releases/download/latest/wappos-debian-preseed.iso)**

Gravez-la sur une clé USB (bare metal) ou montez-la dans votre hyperviseur, puis démarrez dessus. Répondez aux quelques questions Debian standards (langue, clavier, fuseau horaire, partitionnement, nom de machine) — le reste s'installe automatiquement, y compris Wappos, jusqu'à l'affichage des identifiants de connexion.

À la fin de l'installation Debian, la machine s'éteint toute seule. Retirez le support d'installation (clé USB, ou détachez l'ISO virtuelle) puis redémarrez — Wappos s'installe alors tout seul, sans autre intervention.

## Méthode 2 — Sur un Debian 12 déjà installé

```bash
git clone https://github.com/byrtn/wappos-install.git
cd wappos-install
./install-wappos.sh
```

À exécuter en tant que root. Le script installe le socle système, Docker, les composants Wappos, et affiche à la fin l'adresse et les identifiants de connexion.
