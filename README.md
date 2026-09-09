# wappos-install

Installeur Wappos (Debian + composants Wappos). Deux façons d'installer, au choix.

## Méthode 1 — Depuis l'ISO (bare metal ou n'importe quel hyperviseur)

Téléchargez l'ISO déjà construite, prête à l'emploi :

**[Télécharger l'ISO Wappos](https://github.com/byrtn/wappos-install/releases/download/latest/wappos-debian-preseed.iso)**

Gravez-la sur une clé USB (bare metal) ou montez-la dans votre hyperviseur, puis démarrez dessus. Répondez aux quelques questions Debian standards (langue, clavier, fuseau horaire, partitionnement, nom de machine, réseau) — le reste s'installe automatiquement, y compris YunoHost et Wappos, jusqu'à l'affichage des identifiants de connexion.

À la fin de l'installation Debian, la machine **redémarre automatiquement**. Si vous installez depuis une clé USB, retirez-la pendant ce redémarrage pour éviter de relancer l'installateur. Sur un hyperviseur configuré pour démarrer sur le disque en priorité (ordre de démarrage standard), aucune action n'est nécessaire — l'ISO virtuelle peut rester montée. Une fois redémarré, Wappos s'installe alors tout seul, sans autre intervention, jusqu'à l'affichage des identifiants de connexion.

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
et le navigateur, sans jamais avoir besoin de SSH. Le mot de passe root est temporaire,
généré aléatoirement et unique à chaque machine dès l'installation Debian (mis en
cache dans `/root/.wappos-boot-password`, lisible depuis la console si besoin) — il
est de toute façon remplacé automatiquement par le mot de passe de votre compte
administrateur dès la fin du formulaire de configuration initiale.

Si vous avez besoin d'un accès SSH avant la fin de l'installation, une question dédiée
apparaît dans la console tout à la fin du script (juste avant l'affichage des
identifiants) et propose d'activer temporairement la connexion par mot de passe le
temps d'ajouter votre clé publique — elle attend 20 secondes puis passe automatiquement
si vous ne répondez pas, sans rien bloquer. Comme elle survient après le retour du
formulaire du navigateur, il est facile de ne pas la voir défiler si votre attention
est encore sur le navigateur à ce moment-là.

Si vous la manquez (ou si vous en avez besoin bien plus tard), pas de souci : la
commande pour activer l'accès SSH reste **affichée en permanence** à chaque connexion
en console (dans le même bandeau que le portail/l'administration/l'identifiant), tant
que vous ne l'avez pas activé vous-même.
