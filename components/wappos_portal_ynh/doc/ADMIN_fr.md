# Wappos Portal — guide d'administration

Portal BYRTN personnalisé pour wappos.fr : affiche, sous forme de tuiles, les apps déjà
autorisées par les permissions natives de YunoHost pour l'utilisateur connecté, avec en
plus une page d'édition de profil et un écran de connexion personnalisé — le tout délégué
à l'API interne du portail YunoHost (`/yunohost/portalapi/*`), jamais un système
d'authentification maison.

## Ce que cette app ne fait JAMAIS (par conception)

- N'installe/ne supprime/ne gère aucune autre app YunoHost.
- N'implémente aucune vérification de mot de passe elle-même — chaque connexion,
  modification de profil ou vérification de permission est déléguée à YunoHost lui-même
  (`yunohost-portal-api`), authentifié avec l'identité réelle de l'utilisateur connecté.
- Ne maintient aucun catalogue d'apps concurrent. Elle ne fait que refléter ce que l'API
  native `/me` de YunoHost renvoie déjà pour l'utilisateur connecté.

Voir la section 1.2 du CDC pour le détail complet du garde-fou (lié à RFC-0001/DEC-022),
et les sections 9/9bis/9ter pour l'architecture API interne et ses limites connues.

## Fragilité connue

Cette app appelle directement l'API interne du portail YunoHost sur `127.0.0.1:6788` —
un détail d'implémentation interne non documenté, pas une API publique stable. Après
toute montée de version majeure de YunoHost, retester connexion, tuiles et édition de
profil avant de faire confiance à cette app.
