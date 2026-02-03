#!/usr/bin/env python3
"""Fetch unread Gmail messages via IMAP (App Password) and output JSON.

- Only searches UNSEEN in a mailbox.
- Stores processed UID set in gmail/state.json to avoid repeating summaries.
- Does NOT mark messages as read (per user preference).

Output JSON:
{
  runAt, account, mailbox,
  totalUnread, newCount,
  messages: [{uid, from, subject, date, messageId, snippet}]
}

No external dependencies.
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
STATE_PATH = os.path.join(BASE_DIR, "state.json")


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


def strip_html(html: str) -> str:
    html = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.I)
    html = re.sub(r"<style[\s\S]*?</style>", " ", html, flags=re.I)
    html = re.sub(r"<[^>]+>", " ", html)
    html = re.sub(r"\s+", " ", html).strip()
    return html


def extract_text(msg: email.message.Message, max_chars: int = 1200) -> str:
    text_parts: list[str] = []
    html_parts: list[str] = []

    if msg.is_multipart():
        for part in msg.walk():
            ctype = (part.get_content_type() or "").lower()
            disp = (part.get("Content-Disposition") or "").lower()
            if "attachment" in disp:
                continue
            payload = part.get_payload(decode=True)
            if not payload:
                continue
            charset = part.get_content_charset() or "utf-8"
            try:
                s = payload.decode(charset, errors="replace")
            except Exception:
                s = payload.decode("utf-8", errors="replace")

            if ctype == "text/plain":
                text_parts.append(s)
            elif ctype == "text/html":
                html_parts.append(s)
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            try:
                s = payload.decode(charset, errors="replace")
            except Exception:
                s = payload.decode("utf-8", errors="replace")
            ctype = (msg.get_content_type() or "").lower()
            if ctype == "text/plain":
                text_parts.append(s)
            elif ctype == "text/html":
                html_parts.append(s)

    body = "\n".join([p.strip() for p in text_parts if p.strip()]).strip()
    if not body and html_parts:
        body = strip_html("\n".join(html_parts))

    body = re.sub(r"\s+", " ", body).strip()
    if len(body) > max_chars:
        body = body[: max_chars - 1] + "…"
    return body


def main() -> int:
    cfg = load_json(CONFIG_PATH, {})
    state = load_json(STATE_PATH, {"version": 1, "processedUids": []})
    processed = set(str(x) for x in (state.get("processedUids") or []))

    account = cfg.get("account")
    imap_cfg = cfg.get("imap") or {}
    host = imap_cfg.get("host", "imap.gmail.com")
    port = int(imap_cfg.get("port", 993))
    mailbox = imap_cfg.get("mailbox", "INBOX")

    max_messages = int(cfg.get("maxMessages", 30))

    pw_file = (cfg.get("auth") or {}).get("appPasswordFile")
    if not (account and pw_file and os.path.exists(pw_file)):
        raise SystemExit("Missing account or appPasswordFile")
    password = read_secret(pw_file)

    ctx = ssl.create_default_context()
    M = imaplib.IMAP4_SSL(host=host, port=port, ssl_context=ctx)
    try:
        M.login(account, password)
        M.select(mailbox)

        typ, data = M.search(None, "UNSEEN")
        if typ != "OK":
            raise RuntimeError("IMAP search failed")

        ids = data[0].split() if data and data[0] else []
        total_unread = len(ids)

        # Fetch newest first
        ids = list(reversed(ids))

        messages = []
        new_count = 0

        for msg_id in ids:
            if len(messages) >= max_messages:
                break

            # Get UID for stable identity
            typ_uid, uid_data = M.fetch(msg_id, "(UID)")
            uid = None
            if typ_uid == "OK" and uid_data and uid_data[0]:
                m = re.search(rb"UID (\d+)", uid_data[0][0] if isinstance(uid_data[0], tuple) else uid_data[0])
                if m:
                    uid = m.group(1).decode("ascii")

            if uid and uid in processed:
                continue

            typ2, msg_data = M.fetch(msg_id, "(RFC822.HEADER BODY.PEEK[TEXT])")
            if typ2 != "OK" or not msg_data:
                continue

            raw_header = b""
            raw_text = b""
            for part in msg_data:
                if not isinstance(part, tuple):
                    continue
                label = part[0]
                blob = part[1] or b""
                if b"RFC822.HEADER" in label:
                    raw_header += blob
                elif b"BODY[TEXT]" in label:
                    raw_text += blob

            header_msg = email.message_from_bytes(raw_header)

            from_ = decode_mime_words(header_msg.get("From"))
            subject = decode_mime_words(header_msg.get("Subject"))
            date = decode_mime_words(header_msg.get("Date"))
            message_id = decode_mime_words(header_msg.get("Message-Id"))

            snippet = ""
            if raw_text:
                try:
                    snippet = raw_text.decode("utf-8", errors="replace")
                except Exception:
                    snippet = raw_text.decode("latin-1", errors="replace")
                snippet = strip_html(snippet)
                snippet = re.sub(r"\s+", " ", snippet).strip()
                if len(snippet) > 700:
                    snippet = snippet[:699] + "…"

            messages.append({
                "uid": uid or None,
                "from": from_,
                "subject": subject,
                "date": date,
                "messageId": message_id,
                "snippet": snippet,
            })
            new_count += 1

            if uid:
                processed.add(uid)

        # Trim state
        processed_list = list(processed)
        processed_list = processed_list[-5000:]
        state["processedUids"] = processed_list
        state["updatedAt"] = utc_now_iso()
        save_json(STATE_PATH, state)

        out = {
            "runAt": utc_now_iso(),
            "account": account,
            "mailbox": mailbox,
            "totalUnread": total_unread,
            "newCount": new_count,
            "messages": messages,
        }
        print(json.dumps(out, ensure_ascii=False))
        return 0

    finally:
        try:
            M.logout()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
