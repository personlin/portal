#!/usr/bin/env python3
"""Watch for Disney+ login verification emails (OTP) and output JSON.

- Uses IMAP (Gmail) with X-GM-RAW search.
- Looks for likely OTP / verification code subjects.
- DOES NOT include full codes in output (safety): returns masked code if detected.
- Maintains its own state file to avoid duplicate alerts.

Output JSON:
{
  ok, runAt,
  matchCount,
  newCount,
  alerts: [{uid, from, subject, date, codeMasked}]
}

No external deps.
"""

from __future__ import annotations

import email
import imaplib
import json
import os
import re
import ssl
from datetime import datetime, timezone
from email.header import decode_header

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
STATE_PATH = os.path.join(BASE_DIR, "disney_otp_state.json")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: str, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, obj) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def read_secret(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def decode_mime_words(s: str | None) -> str:
    if not s:
        return ""
    parts = []
    for v, enc in decode_header(s):
        if isinstance(v, bytes):
            try:
                parts.append(v.decode(enc or "utf-8", errors="replace"))
            except Exception:
                parts.append(v.decode("utf-8", errors="replace"))
        else:
            parts.append(v)
    return "".join(parts).strip()


def mask_code(code: str) -> str:
    code = (code or "").strip()
    if not code:
        return ""
    # Keep only last 3 digits
    digits = re.sub(r"\D+", "", code)
    if len(digits) <= 3:
        return "***"
    return "***" + digits[-3:]


def extract_code_from_subject(subject: str) -> str:
    # Very conservative: look for 4-8 digit sequences
    m = re.search(r"\b(\d{4,8})\b", subject or "")
    return m.group(1) if m else ""


def main() -> int:
    cfg = load_json(CONFIG_PATH, {})
    state = load_json(STATE_PATH, {"version": 1, "processedUids": []})
    processed = set(str(x) for x in (state.get("processedUids") or []))

    account = cfg.get("account")
    imap_cfg = cfg.get("imap") or {}
    host = imap_cfg.get("host", "imap.gmail.com")
    port = int(imap_cfg.get("port", 993))
    mailbox = imap_cfg.get("mailbox", "INBOX")

    pw_file = (cfg.get("auth") or {}).get("appPasswordFile")
    if not (account and pw_file and os.path.exists(pw_file)):
        print(json.dumps({"ok": False, "error": "missing_account_or_appPasswordFile"}, ensure_ascii=False))
        return 2

    password = read_secret(pw_file)

    # Gmail raw search: Disney+ sender + OTP-ish subjects.
    raw_query = (
        'from:(disneyplus@trx.mail2.disneyplus.com) '
        '(subject:("一次性驗證碼") OR subject:("verification") OR subject:("code") OR subject:("OTP")) '
        'is:unread'
    )

    ctx = ssl.create_default_context()
    M = imaplib.IMAP4_SSL(host=host, port=port, ssl_context=ctx)
    try:
        M.login(account, password)
        M.select(mailbox)

        typ, data = M.uid('SEARCH', None, 'X-GM-RAW', raw_query)
        if typ != 'OK':
            raise RuntimeError('imap_search_failed')

        uids = data[0].split() if data and data[0] else []
        match_count = len(uids)

        alerts = []
        # newest first
        for uid in reversed(uids[-20:]):
            uid_s = uid.decode() if isinstance(uid, bytes) else str(uid)
            if uid_s in processed:
                continue

            typ2, msg_data = M.uid('FETCH', uid, '(RFC822.HEADER)')
            if typ2 != 'OK' or not msg_data:
                continue

            raw = b''
            for part in msg_data:
                if isinstance(part, tuple):
                    raw += part[1] or b''

            h = email.message_from_bytes(raw)
            from_ = decode_mime_words(h.get('From'))
            subject = decode_mime_words(h.get('Subject'))
            date = decode_mime_words(h.get('Date'))

            code = extract_code_from_subject(subject)
            alerts.append({
                'uid': uid_s,
                'from': from_,
                'subject': subject,
                'date': date,
                'codeMasked': mask_code(code),
            })

            processed.add(uid_s)

        # persist state
        state['processedUids'] = sorted(processed, key=lambda x: int(x))[-500:]
        save_json(STATE_PATH, state)

        out = {
            'ok': True,
            'runAt': utc_now_iso(),
            'query': raw_query,
            'matchCount': match_count,
            'newCount': len(alerts),
            'alerts': alerts,
        }
        print(json.dumps(out, ensure_ascii=False))
        return 0
    finally:
        try:
            M.logout()
        except Exception:
            pass


if __name__ == '__main__':
    raise SystemExit(main())
