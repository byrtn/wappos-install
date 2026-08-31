# Wappos Portal — admin guide

Custom BYRTN-branded portal for wappos.fr: shows the same apps a user's YunoHost
permissions already grant them, as tiles, plus a profile-editing page and a custom
login screen — all delegated to YunoHost's own internal portal API
(`/yunohost/portalapi/*`), never a home-grown authentication system.

## What this app does NOT do (by design)

- Does not install/remove/manage other YunoHost apps.
- Does not implement its own authentication or password verification — every login,
  profile change, and permission check is delegated to YunoHost itself
  (`yunohost-portal-api`), authenticated as the real logged-in user.
- Does not maintain a competing app catalog. It only ever reflects what YunoHost's own
  `/me` endpoint already reports for the connected user.

See the project CDC's section 1.2 for the full guard rail rationale (tied to
RFC-0001/DEC-022), and sections 9/9bis/9ter for the internal-API architecture and its
known limitations.

## Known fragility

This app calls YunoHost's internal portal API directly on `127.0.0.1:6788` — an
undocumented internal implementation detail, not a stable public API. After any major
YunoHost core upgrade, retest login, tiles, and profile editing before relying on this
app again.
