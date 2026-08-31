# Auteur : Patrick Ritaine
import mailbox
import os
import re
import subprocess
import sys
from email.header import decode_header, make_header
from email.message import EmailMessage

_ARGS = sys.argv[1:]
ALERT_TO = _ARGS[0] if _ARGS else "root"
ALERT_MBOX = _ARGS[1] if len(_ARGS) > 1 else "/var/mail/cron.alerts"

_KNOWN_NOISE_PATTERNS = [
    re.compile(r"/dev/shm/rhm\.[0-9a-f]+"),
]


def _decode_subject(raw: str | None) -> str:
    if not raw:
        return "(sans sujet)"
    try:
        return str(make_header(decode_header(raw)))
    except (ValueError, UnicodeDecodeError):
        return raw


def _message_text(message) -> str:
    if message.is_multipart():
        parts = []
        for part in message.walk():
            if part.get_content_maintype() == "text":
                parts.append(_payload_text(part))
        return "\n".join(parts)
    return _payload_text(message)


def _payload_text(part) -> str:
    payload = part.get_payload(decode=True)
    if payload is None:
        payload_str = part.get_payload()
        return payload_str if isinstance(payload_str, str) else ""
    charset = part.get_content_charset() or "utf-8"
    try:
        return payload.decode(charset, errors="replace")
    except LookupError:
        return payload.decode("utf-8", errors="replace")


def _read_messages() -> list[dict]:
    if not os.path.isfile(ALERT_MBOX) or os.path.getsize(ALERT_MBOX) == 0:
        return []
    box = mailbox.mbox(ALERT_MBOX)
    try:
        box.lock()
    except (mailbox.ExternalClashError, OSError) as e:
        print(f"Boite {ALERT_MBOX} verrouillee, report au prochain passage : {e}", file=sys.stderr)
        return []
    try:
        return [
            {"subject": _decode_subject(m.get("Subject")), "text": _message_text(m)}
            for m in box
        ]
    finally:
        box.unlock()
        box.close()


def _empty_mbox() -> None:
    try:
        with open(ALERT_MBOX, "r+") as handle:
            handle.truncate(0)
    except OSError as e:
        print(f"Vidage de {ALERT_MBOX} impossible : {e}", file=sys.stderr)
        raise


def _is_pure_noise(text: str) -> bool:
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if "Warning:" in line:
            block = [line]
            j = i + 1
            while j < len(lines) and lines[j].strip() and "Warning:" not in lines[j]:
                block.append(lines[j])
                j += 1
            block_text = "\n".join(block)
            if not any(pattern.search(block_text) for pattern in _KNOWN_NOISE_PATTERNS):
                return False
            i = j
        else:
            i += 1
    return True


def _classify(message: dict) -> dict:
    text = message.get("text", "")
    is_error_exit = "run-parts" in text and "exit status" in text and "exit status 0" not in text
    if is_error_exit:
        return {"silence": False, "reason": "code de sortie non nul"}
    if _is_pure_noise(text):
        return {"silence": True, "reason": "faux positif connu, sans action requise"}
    return {"silence": False, "reason": "contenu non reconnu comme bénin"}


def _send_summary(kept: list[dict]) -> None:
    if not kept:
        return
    msg = EmailMessage()
    msg["From"] = "wappos-admin-mail-filter@localhost"
    msg["To"] = ALERT_TO
    count = len(kept)
    msg["Subject"] = f"[wappos-admin] {count} alerte(s) système à vérifier"

    sections = []
    for item in kept:
        sections.append(
            f"=== {item['message']['subject']} ===\n"
            f"Raison : {item['reason']}\n\n"
            f"{item['message']['text']}"
        )

    body = (
        f"{count} message(s) technique(s) reçu(s) sur la boîte de surveillance, "
        "jugé(s) suffisamment inhabituel(s) pour être transmis tels quels :\n\n"
        + "\n\n".join(sections)
    )
    msg.set_content(body, charset="utf-8")

    result = subprocess.run(
        ["doveadm", "save", "-u", ALERT_TO, "-m", "INBOX"],
        input=msg.as_bytes(), capture_output=True, timeout=60,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        print(f"Depot du resume dans la boite de {ALERT_TO} impossible : {detail}", file=sys.stderr)
        raise RuntimeError(detail or "doveadm save a echoue")


def main() -> None:
    messages = _read_messages()
    if not messages:
        return
    kept = []
    for message in messages:
        verdict = _classify(message)
        if not verdict["silence"]:
            kept.append({"message": message, "reason": verdict["reason"]})
    _send_summary(kept)
    _empty_mbox()


if __name__ == "__main__":
    main()
