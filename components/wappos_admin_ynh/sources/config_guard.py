# Auteur : Patrick Ritaine
import json
import smtplib
import subprocess
import sys
from email.message import EmailMessage

ALERT_TO = sys.argv[1] if len(sys.argv) > 1 else "root"

GUARDED_FRAGMENTS = {
    "dev.byrtn.fr": {
        "path": "/etc/nginx/conf.d/dev.byrtn.fr.d/dev-byrtn-public-static.conf",
        "content": (
            'location = /robots.txt {\n'
            '    access_by_lua_block { return; }\n'
            '    default_type text/plain;\n'
            '    return 200 "User-agent: *\\nDisallow:\\n";\n'
            '}\n'
            '\n'
            'location = /sitemap.xml {\n'
            '    access_by_lua_block { return; }\n'
            '    default_type application/xml;\n'
            '    return 200 "<?xml version=\\"1.0\\" encoding=\\"UTF-8\\"?><urlset xmlns=\\"http://www.sitemaps.org/schemas/sitemap/0.9\\"></urlset>";\n'
            '}\n'
            '\n'
            'location = /favicon.ico {\n'
            '    access_by_lua_block { return; }\n'
            '    return 204;\n'
            '}\n'
            '\n'
            'location = / {\n'
            '    access_by_lua_file /usr/share/ssowat/access.lua;\n'
            '}\n'
            '\n'
            'error_page 404 /404-byrtn.html;\n'
            '\n'
            'location = /404-byrtn.html {\n'
            '    internal;\n'
            '    root /var/www/byrtn-errors;\n'
            '    access_by_lua_block { return; }\n'
            '}\n'
            '\n'
            'location / {\n'
            '    access_by_lua_block { return; }\n'
            '    return 404;\n'
            '}\n'
        ),
    },
    "dev.wappos.fr": {
        "path": "/etc/nginx/conf.d/dev.wappos.fr.d/dev-wappos-public-static.conf",
        "content": (
            'location = /robots.txt {\n'
            '    access_by_lua_block { return; }\n'
            '    default_type text/plain;\n'
            '    return 200 "User-agent: *\\nDisallow:\\n";\n'
            '}\n'
            '\n'
            'location = /sitemap.xml {\n'
            '    access_by_lua_block { return; }\n'
            '    default_type application/xml;\n'
            '    return 200 "<?xml version=\\"1.0\\" encoding=\\"UTF-8\\"?><urlset xmlns=\\"http://www.sitemaps.org/schemas/sitemap/0.9\\"></urlset>";\n'
            '}\n'
            '\n'
            'location = /favicon.ico {\n'
            '    access_by_lua_block { return; }\n'
            '    return 204;\n'
            '}\n'
            '\n'
            'location = / {\n'
            '    access_by_lua_file /usr/share/ssowat/access.lua;\n'
            '}\n'
            '\n'
            'error_page 404 /404-wappos.html;\n'
            '\n'
            'location = /404-wappos.html {\n'
            '    internal;\n'
            '    root /var/www/wappos-errors;\n'
            '    access_by_lua_block { return; }\n'
            '}\n'
            '\n'
            'location / {\n'
            '    access_by_lua_block { return; }\n'
            '    return 404;\n'
            '}\n'
        ),
    },
    "photography.dev.byrtn.fr": {
        "path": "/etc/nginx/conf.d/photography.dev.byrtn.fr.d/photography-dev-public-static.conf",
        "content": (
            'location = /robots.txt {\n'
            '    access_by_lua_block { return; }\n'
            '    default_type text/plain;\n'
            '    return 200 "User-agent: *\\nDisallow:\\n";\n'
            '}\n'
            '\n'
            'location = /sitemap.xml {\n'
            '    access_by_lua_block { return; }\n'
            '    default_type application/xml;\n'
            '    return 200 "<?xml version=\\"1.0\\" encoding=\\"UTF-8\\"?><urlset xmlns=\\"http://www.sitemaps.org/schemas/sitemap/0.9\\"></urlset>";\n'
            '}\n'
            '\n'
            'location = /favicon.ico {\n'
            '    access_by_lua_block { return; }\n'
            '    return 204;\n'
            '}\n'
            '\n'
            'location = / {\n'
            '    access_by_lua_block { return; }\n'
            '    return 301 https://photography.dev.byrtn.fr/soon;\n'
            '}\n'
            '\n'
            'error_page 404 /404-photography.html;\n'
            '\n'
            'location = /404-photography.html {\n'
            '    internal;\n'
            '    root /var/www/photography-errors;\n'
            '    access_by_lua_block { return; }\n'
            '}\n'
            '\n'
            'location / {\n'
            '    access_by_lua_block { return; }\n'
            '    return 404;\n'
            '}\n'
        ),
    },
}


def _current_domains() -> set[str]:
    try:
        out = subprocess.run(
            ["yunohost", "domain", "list", "--output-as", "json"],
            capture_output=True, text=True, timeout=15, check=True,
        ).stdout
        return set(json.loads(out).get("domains", []))
    except Exception:
        return set(GUARDED_FRAGMENTS.keys())


def _check_and_fix() -> list[tuple[str, str, str]]:
    results = []
    domains = _current_domains()
    nginx_touched = False

    for domain, spec in GUARDED_FRAGMENTS.items():
        if domain not in domains:
            results.append((domain, "SKIP", "domaine plus hébergé sur cette VM, fragment ignoré"))
            continue

        from pathlib import Path
        path = Path(spec["path"])
        expected = spec["content"]

        try:
            current = path.read_text() if path.exists() else None
        except OSError as e:
            results.append((domain, "ERROR", f"lecture impossible : {e}"))
            continue

        if current == expected:
            results.append((domain, "OK", ""))
            continue

        status = "MISSING" if current is None else "DRIFTED"
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(expected)
            nginx_touched = True
            results.append((domain, status, "corrigé automatiquement"))
        except OSError as e:
            results.append((domain, status, f"échec de la correction automatique : {e}"))

    if nginx_touched:
        test = subprocess.run(["nginx", "-t"], capture_output=True, text=True)
        if test.returncode == 0:
            subprocess.run(["systemctl", "reload", "nginx"], check=False)
        else:
            results.append(("nginx", "ERROR", f"`nginx -t` a échoué après correction : {test.stderr.strip()}"))

    return results


CROSSDOMAIN_MARKER = "rewrite ^/yunohost/sso/"
CROSSDOMAIN_HOOK = "/etc/yunohost/hooks.d/post_domain_add/50-wappos-sso-bypass"


def _check_crossdomain_hook() -> list[tuple[str, str, str]]:
    from pathlib import Path

    results = []
    for domain in _current_domains():
        frag = Path(f"/etc/nginx/conf.d/{domain}.d/wappos_sso_bypass.conf")
        label = f"{domain} (contournement SSO natif)"

        try:
            current = frag.read_text() if frag.exists() else ""
        except OSError as e:
            results.append((label, "ERROR", f"lecture impossible : {e}"))
            continue

        if CROSSDOMAIN_MARKER in current:
            results.append((label, "OK", ""))
            continue

        status = "MISSING" if not frag.exists() else "DRIFTED"
        regen = subprocess.run(
            ["bash", CROSSDOMAIN_HOOK, domain], capture_output=True, text=True,
        )
        if regen.returncode == 0:
            results.append((label, status, "régénéré automatiquement via le hook officiel"))
        else:
            results.append((label, status, f"échec de la régénération : {regen.stderr.strip()}"))

    return results


_MOUNT_FSTYPE_DENYLIST = {
    "tmpfs", "devtmpfs", "proc", "sysfs", "cgroup", "cgroup2", "pstore",
    "bpf", "tracefs", "debugfs", "mqueue", "hugetlbfs", "devpts",
    "securityfs", "autofs", "overlay", "squashfs", "efivarfs", "configfs",
    "fusectl", "binfmt_misc", "rpc_pipefs", "nsfs",
}

DISK_WARNING_PERCENT = 85
DISK_CRITICAL_PERCENT = 95


def _check_disk_thresholds() -> list[tuple[str, str, str]]:
    import os

    results = []
    seen_devices: set[str] = set()
    with open("/proc/mounts", "r", encoding="utf-8") as f:
        for line in f:
            parts = line.split()
            if len(parts) < 3:
                continue
            device, mountpoint, fstype = parts[0], parts[1], parts[2]
            if fstype in _MOUNT_FSTYPE_DENYLIST or not device.startswith("/dev/"):
                continue
            if device in seen_devices:
                continue
            try:
                stat = os.statvfs(mountpoint)
            except OSError:
                continue
            total = stat.f_frsize * stat.f_blocks
            if total == 0:
                continue
            used = total - (stat.f_frsize * stat.f_bfree)
            percent = round((used / total) * 100, 1)
            seen_devices.add(device)

            label = f"disque {mountpoint}"
            if percent >= DISK_CRITICAL_PERCENT:
                results.append((label, "CRITICAL", f"{percent}% utilisé — intervention rapide recommandée"))
            elif percent >= DISK_WARNING_PERCENT:
                results.append((label, "WARNING", f"{percent}% utilisé"))
            else:
                results.append((label, "OK", f"{percent}% utilisé"))
    return results


def _check_failed_units() -> list[tuple[str, str, str]]:
    results = []
    out = subprocess.run(
        ["systemctl", "list-units", "--all", "--state=failed", "--no-legend", "--plain"],
        capture_output=True, text=True,
    ).stdout
    for line in out.splitlines():
        parts = line.split(None, 4)
        if not parts:
            continue
        unit = parts[0]
        description = parts[4] if len(parts) > 4 else unit
        results.append((f"service {unit}", "CRITICAL", f"en échec — {description}"))
    return results


def _send_report(results: list[tuple[str, str, str]]) -> None:
    msg = EmailMessage()
    msg["From"] = "wappos-admin-config-guard@localhost"
    msg["To"] = ALERT_TO
    msg["Subject"] = "[wappos-admin] Vérification quotidienne du serveur — anomalie détectée"

    lines = [
        f"- {domain} : {status}" + (f" — {detail}" if detail else "")
        for domain, status, detail in results
    ]
    body = (
        "Vérification quotidienne (personnalisations nginx hors du périmètre "
        "géré automatiquement par YunoHost, occupation disque, et services "
        "système en échec) — au moins un écart a été détecté :\n\n" + "\n".join(lines) +
        "\n\nSTATUTS possibles — configuration : OK (conforme), MISSING (absent, "
        "recréé), DRIFTED (contenu différent, corrigé), SKIP (domaine plus "
        "hébergé ici), ERROR (correction échouée — intervention manuelle "
        f"nécessaire). Disque : OK (sous {DISK_WARNING_PERCENT}%), WARNING "
        f"(au moins {DISK_WARNING_PERCENT}% utilisé), CRITICAL (au moins "
        f"{DISK_CRITICAL_PERCENT}% utilisé — intervention rapide recommandée). "
        "Services système : CRITICAL (service ou minuterie en échec — intervention "
        "manuelle nécessaire, ce correctif n'est jamais appliqué automatiquement)."
    )
    msg.set_content(body, charset="utf-8")

    smtp = smtplib.SMTP("localhost")
    smtp.send_message(msg)
    smtp.quit()


def main() -> None:
    results = _check_and_fix() + _check_crossdomain_hook() + _check_disk_thresholds() + _check_failed_units()
    if any(status in ("MISSING", "DRIFTED", "ERROR", "WARNING", "CRITICAL") for _, status, _ in results):
        _send_report(results)


if __name__ == "__main__":
    main()
