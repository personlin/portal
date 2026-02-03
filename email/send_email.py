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
    p.add_argument("--text", default=None)
    p.add_argument("--text-file", default=None)
    p.add_argument("--app-password-file", required=True)
    p.add_argument("--smtp-host", default="smtp.gmail.com")
    p.add_argument("--smtp-port", type=int, default=587)
    args = p.parse_args()

    if not args.text and not args.text_file:
        raise SystemExit("Provide --text or --text-file")

    body = args.text if args.text is not None else read_file(args.text_file)
    app_pw = read_file(args.app_password_file).strip()

    msg = EmailMessage()
    msg["From"] = args.from_addr
    msg["To"] = args.to_addr
    msg["Subject"] = args.subject
    msg.set_content(body)

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
