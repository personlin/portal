#!/usr/bin/env python3
"""Send an email via SMTP (Gmail) using an App Password.

Usage:
  python3 send_email.py \
    --from p0937087703@gmail.com \
    --to personlin@gmail.com \
    --subject "..." \
    --text-file /tmp/body.txt \
    --app-password-file /home/person/.openclaw/credentials/gmail-p0937087703-app-password.txt

No external deps.
"""

from __future__ import annotations

import argparse
import os
import smtplib
import ssl
from email.message import EmailMessage


def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--from", dest="from_addr", required=True)
    p.add_argument("--to", dest="to_addr", required=True)
    p.add_argument("--subject", required=True)

    # Plain text
    p.add_argument("--text", default=None)
    p.add_argument("--text-file", default=None)

    # Optional HTML (will be sent as multipart/alternative with text fallback)
    p.add_argument("--html", default=None)
    p.add_argument("--html-file", default=None)

    p.add_argument("--app-password-file", required=True)
    p.add_argument("--smtp-host", default="smtp.gmail.com")
    p.add_argument("--smtp-port", type=int, default=587)
    args = p.parse_args()

    if not (args.text or args.text_file or args.html or args.html_file):
        raise SystemExit("Provide --text/--text-file and/or --html/--html-file")

    body_text = args.text if args.text is not None else (read_file(args.text_file) if args.text_file else None)
    body_html = args.html if args.html is not None else (read_file(args.html_file) if args.html_file else None)

    # If only HTML is provided, derive a minimal text fallback.
    if body_text is None and body_html is not None:
        body_text = "(此郵件包含 HTML 內容；若你看到這行代表你的郵件客戶端未顯示 HTML。)"

    app_pw = read_file(args.app_password_file).strip()

    msg = EmailMessage()
    msg["From"] = args.from_addr
    msg["To"] = args.to_addr
    msg["Subject"] = args.subject

    msg.set_content(body_text or "")
    if body_html is not None:
        msg.add_alternative(body_html, subtype="html")

    ctx = ssl.create_default_context()
    with smtplib.SMTP(args.smtp_host, args.smtp_port, timeout=30) as s:
        s.ehlo()
        s.starttls(context=ctx)
        s.ehlo()
        s.login(args.from_addr, app_pw)
        s.send_message(msg)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
