# wappos-install

Installeur Wappos (YunoHost + composants Wappos). Deux façons d'installer, au choix.

## Méthode 1 — Depuis l'ISO (bare metal ou n'importe quel hyperviseur)

Téléchargez l'ISO déjà construite, prête à l'emploi :

**[Télécharger l'ISO Wappos](https://github.com/byrtn/wappos-install/releases/download/latest/wappos-debian-preseed.iso)**

Gravez-la sur une clé USB (bare metal) ou montez-la dans votre hyperviseur, puis démarrez dessus. Répondez aux quelques questions Debian standards (langue, clavier, fuseau horaire, partitionnement, nom de machine, réseau) — le reste s'installe automatiquement, y compris Wappos, jusqu'à l'affichage des identifiants de connexion.

À la fin de l'installation Debian, la machine s'éteint toute seule. Retirez le support d'installation (clé USB, ou détachez l'ISO virtuelle) puis redémarrez — Wappos s'installe alors tout seul, sans autre intervention.

## Méthode 2 — Sur un Debian 12 déjà installé

```bash
git clone https://github.com/byrtn/wappos-install.git
cd wappos-install
./install-wappos.sh
```

À exécuter en tant que root. Le script installe le socle système, Docker, les composants Wappos, et affiche à la fin l'adresse et les identifiants de connexion.

## Important — pendant l'installation

La connexion SSH par mot de passe est **désactivée dès le premier démarrage** (seules
les clés SSH sont acceptées) : l'installation se pilote entièrement depuis la console
et le navigateur, sans jamais avoir besoin de SSH. Le mot de passe root est temporaire
et fixe (`wapposinstall`, visible dans `preseed.cfg`) — il ne sert qu'à une éventuelle
connexion console, et est de toute façon remplacé automatiquement par le mot de passe
de votre compte administrateur dès la fin du formulaire de configuration initiale.

Si vous avez besoin d'un accès SSH avant la fin de l'installation, l'étape dédiée en
fin de script permet d'activer temporairement la connexion par mot de passe le temps
d'ajouter votre clé publique.
