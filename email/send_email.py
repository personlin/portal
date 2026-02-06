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
import time
from email.message import EmailMessage


def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def append_jsonl(path: str, obj: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    line = (json_dumps(obj) + "\n")
    with open(path, "a", encoding="utf-8") as f:
        f.write(line)


def json_dumps(obj: dict) -> str:
    import json

    return json.dumps(obj, ensure_ascii=False)


def parse_backoff(s: str) -> list[int]:
    out: list[int] = []
    for part in (s or "").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            out.append(max(0, int(float(part))))
        except Exception:
            continue
    return out


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

    # Reliability
    p.add_argument("--timeout", type=int, default=30, help="SMTP timeout seconds")
    p.add_argument("--retries", type=int, default=3, help="Max attempts")
    p.add_argument("--retry-backoff", default="5,15,45", help="Comma-separated seconds")
    p.add_argument("--log", default=None, help="Append JSONL log to this path")

    args = p.parse_args()
    # Parse backoff now; retry behavior added in later steps.
    _backoff = parse_backoff(args.retry_backoff)

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

    started_at = time.time()
    log_path = args.log

    # Step 2B-3c: Enable retries with backoff on failure.
    max_attempts = int(args.retries) if int(args.retries) > 0 else 1
    attempts_effective = max_attempts

    last_err: Exception | None = None

    for attempt in range(1, attempts_effective + 1):
        try:
            ctx = ssl.create_default_context()
            with smtplib.SMTP(args.smtp_host, args.smtp_port, timeout=int(args.timeout)) as s:
                s.ehlo()
                s.starttls(context=ctx)
                s.ehlo()
                s.login(args.from_addr, app_pw)
                s.send_message(msg)

            if log_path:
                append_jsonl(log_path, {
                    "ts": int(time.time()),
                    "ok": True,
                    "attempt": attempt,
                    "maxAttempts": max_attempts,
                    "from": args.from_addr,
                    "to": args.to_addr,
                    "subject": args.subject,
                    "smtpHost": args.smtp_host,
                    "smtpPort": args.smtp_port,
                    "timeout": int(args.timeout),
                    "durationMs": int((time.time() - started_at) * 1000),
                })

            return 0

        except Exception as e:
            last_err = e

            wait_s = 0
            if attempt < attempts_effective:
                if _backoff:
                    wait_s = _backoff[min(attempt - 1, len(_backoff) - 1)]
                else:
                    wait_s = 5

            if log_path:
                append_jsonl(log_path, {
                    "ts": int(time.time()),
                    "ok": False,
                    "attempt": attempt,
                    "maxAttempts": max_attempts,
                    "from": args.from_addr,
                    "to": args.to_addr,
                    "subject": args.subject,
                    "smtpHost": args.smtp_host,
                    "smtpPort": args.smtp_port,
                    "timeout": int(args.timeout),
                    "durationMs": int((time.time() - started_at) * 1000),
                    "error": f"{type(e).__name__}: {e}",
                    "nextWaitSec": wait_s,
                })

            if wait_s and attempt < attempts_effective:
                time.sleep(wait_s)

    # If all attempts failed, raise the last error.
    if last_err is not None:
        raise last_err

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
