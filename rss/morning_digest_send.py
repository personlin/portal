#!/usr/bin/env python3
"""Send the morning digest from the persisted outbox payload.

Step 2C-2: can send EMAIL from outbox and write back send status.
(Default behavior still validates only unless --send-email is provided.)

Reads:
- rss/outbox/morning-YYYY-MM-DD.json (today in Asia/Taipei)
- Optional sidecar files:
  - rss/outbox/morning-YYYY-MM-DD.email.txt
  - rss/outbox/morning-YYYY-MM-DD.email.html

Outputs JSON to stdout with validation info.

No external deps.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import sys

# allow importing rss.db when run as script
WORKSPACE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_PATH not in sys.path:
    sys.path.insert(0, WORKSPACE_PATH)

from rss.db import rss_store  # type: ignore

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(BASE_DIR)
OUTBOX_DIR = os.path.join(BASE_DIR, "outbox")
SEND_EMAIL = os.path.join(WORKSPACE, "email", "send_email.py")
EMAIL_LOG = os.path.join(OUTBOX_DIR, "email_send_log.jsonl")
APP_PW_FILE = "/home/person/.openclaw/credentials/gmail-p0937087703-app-password.txt"
DB_PATH = os.path.join(BASE_DIR, "db", "geosci_rss.sqlite")
DIGEST_KIND = "morning_digest"


def taipei_date() -> str:
    return datetime.now(ZoneInfo("Asia/Taipei")).date().isoformat()


def paths(date_tpe: str) -> tuple[str, str, str]:
    base = os.path.join(OUTBOX_DIR, f"morning-{date_tpe}")
    return base + ".json", base + ".email.txt", base + ".email.html"


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def upsert_digest_delivery(*, date_tpe: str, channel: str, target: str, status: str, batch_id: str | None, error: str | None) -> None:
    # DB should already exist, but init_db is idempotent.
    conn = rss_store.connect(DB_PATH)
    rss_store.init_db(conn)
    now = rss_store.utc_now_iso()
    conn.execute(
        """
        INSERT INTO digest_deliveries(kind,date_taipei,channel,target,batch_id,status,created_at_utc,sent_at_utc,error)
        VALUES (?,?,?,?,?,?,?,?,?)
        ON CONFLICT(kind,date_taipei,channel,target) DO UPDATE SET
          batch_id=excluded.batch_id,
          status=excluded.status,
          sent_at_utc=excluded.sent_at_utc,
          error=excluded.error
        """,
        (
            DIGEST_KIND,
            date_tpe,
            channel,
            target,
            batch_id,
            status,
            now,
            now if status == "sent" else None,
            error,
        ),
    )
    conn.commit()


def db_digest_status(*, date_tpe: str, channel: str, target: str) -> dict | None:
    conn = rss_store.connect(DB_PATH)
    rss_store.init_db(conn)
    row = conn.execute(
        "SELECT status, sent_at_utc, error, batch_id FROM digest_deliveries WHERE kind=? AND date_taipei=? AND channel=? AND target=?",
        (DIGEST_KIND, date_tpe, channel, target),
    ).fetchone()
    if not row:
        return None
    return {"status": row[0], "sentAtUtc": row[1], "error": row[2], "batchId": row[3]}


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None, help="Asia/Taipei date YYYY-MM-DD (default today)")
    ap.add_argument("--send-email", action="store_true", help="Actually send the email")
    ap.add_argument("--force-email", action="store_true", help="Send even if DB says sent")
    ap.add_argument("--subject-prefix", default="", help="Prefix for subject (testing)")
    ap.add_argument("--timeout", type=int, default=30)
    ap.add_argument("--retries", type=int, default=3)
    ap.add_argument("--retry-backoff", default="5,15,45")

    # Telegram workflow is tool-driven (functions.message). This script helps by
    # emitting the message text + writing back send status.
    ap.add_argument("--status", action="store_true", help="Print current sendStatus for today/date")
    ap.add_argument("--get-telegram", action="store_true", help="Print telegram text to stdout")
    ap.add_argument("--mark-telegram-sent", action="store_true", help="Mark telegram as sent in outbox JSON")
    ap.add_argument("--telegram-ok", action="store_true", help="When marking sent, set ok=true")
    ap.add_argument("--telegram-error", default=None, help="When marking sent, record last error")

    args = ap.parse_args()

    date_tpe = args.date or taipei_date()
    json_path, txt_path, html_path = paths(date_tpe)

    out = {
        "dateTaipei": date_tpe,
        "paths": {"json": json_path, "emailTxt": txt_path, "emailHtml": html_path},
        "exists": {
            "json": os.path.exists(json_path),
            "emailTxt": os.path.exists(txt_path),
            "emailHtml": os.path.exists(html_path),
        },
        "email": {},
        "telegram": {},
    }

    if not os.path.exists(json_path):
        out["ok"] = False
        out["error"] = "missing_outbox_json"
        print(json.dumps(out, ensure_ascii=False))
        return 2

    payload = json.load(open(json_path, "r", encoding="utf-8"))

    # Ensure metadata section for send status
    meta = payload.setdefault("sendStatus", {})
    email_meta = meta.setdefault("email", {})
    tg_meta = meta.setdefault("telegram", {})

    # Prefer sidecar files if present
    email_text = read_text(txt_path) if os.path.exists(txt_path) else (payload.get("email") or {}).get("text") or ""
    email_html = read_text(html_path) if os.path.exists(html_path) else (payload.get("email") or {}).get("html") or ""

    out["email"] = {
        "to": (payload.get("email") or {}).get("to"),
        "from": (payload.get("email") or {}).get("from"),
        "subject": (payload.get("email") or {}).get("subject"),
        "textLen": len(email_text or ""),
        "htmlLen": len(email_html or ""),
        "alreadySentAtUtc": email_meta.get("sentAtUtc"),
        "alreadyOk": email_meta.get("ok"),
    }

    tg_text = (payload.get("telegram") or {}).get("text") or ""
    out["telegram"] = {
        "textLen": len(tg_text),
        "alreadySentAtUtc": tg_meta.get("sentAtUtc"),
        "alreadyOk": tg_meta.get("ok"),
    }

    # Optional: send email
    out["sendEmailAttempted"] = False
    out["sendEmailDidSend"] = False

    # Optional: telegram helper operations
    out["getTelegram"] = False
    out["markTelegramSent"] = False

    if args.status:
        email_to = str((payload.get("email") or {}).get("to") or "")
        print(json.dumps({
            "ok": True,
            "dateTaipei": date_tpe,
            "outbox": {
                "email": meta.get("email", {}),
                "telegram": meta.get("telegram", {}),
            },
            "db": {
                "email": db_digest_status(date_tpe=date_tpe, channel="email", target=email_to),
                "telegram": db_digest_status(date_tpe=date_tpe, channel="telegram", target="401392371"),
            }
        }, ensure_ascii=False))
        return 0

    if args.get_telegram:
        out["getTelegram"] = True
        print(tg_text)
        return 0

    if args.mark_telegram_sent:
        out["markTelegramSent"] = True
        tg_meta.update({
            "ok": bool(args.telegram_ok),
            "sentAtUtc": utc_now_iso() if args.telegram_ok else None,
            "lastError": args.telegram_error,
        })
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        batch_id = f"morning-{date_tpe}"
        if args.telegram_ok:
            upsert_digest_delivery(
                date_tpe=date_tpe,
                channel="telegram",
                target="401392371",
                status="sent",
                batch_id=batch_id,
                error=None,
            )
        else:
            upsert_digest_delivery(
                date_tpe=date_tpe,
                channel="telegram",
                target="401392371",
                status="failed",
                batch_id=batch_id,
                error=args.telegram_error,
            )

        print(json.dumps({"ok": True, "marked": True, "telegram": tg_meta}, ensure_ascii=False))
        return 0

    if args.send_email:
        out["sendEmailAttempted"] = True

        email_to = str((payload.get("email") or {}).get("to") or "")
        db_stat = db_digest_status(date_tpe=date_tpe, channel="email", target=email_to)

        if db_stat and db_stat.get("status") == "sent" and not args.force_email:
            out["sendEmailDidSend"] = False
            out["sendEmailSkippedReason"] = "db_already_sent"
        elif email_meta.get("ok") is True and email_meta.get("sentAtUtc") and not args.force_email:
            # legacy fallback
            out["sendEmailDidSend"] = False
            out["sendEmailSkippedReason"] = "outbox_already_sent"
        else:
            subj = (payload.get("email") or {}).get("subject") or "(no subject)"
            subj = args.subject_prefix + subj

            # Write sidecar files (ensure they exist for send_email.py)
            os.makedirs(OUTBOX_DIR, exist_ok=True)
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(email_text)
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(email_html)

            cmd = [
                "python3",
                SEND_EMAIL,
                "--from",
                (payload.get("email") or {}).get("from") or "",
                "--to",
                (payload.get("email") or {}).get("to") or "",
                "--subject",
                subj,
                "--text-file",
                txt_path,
                "--html-file",
                html_path,
                "--app-password-file",
                APP_PW_FILE,
                "--timeout",
                str(int(args.timeout)),
                "--retries",
                str(int(args.retries)),
                "--retry-backoff",
                str(args.retry_backoff),
                "--log",
                EMAIL_LOG,
            ]

            t0 = time.time()
            # batch_id is stable per day (helps dedupe); use outbox base key.
            batch_id = f"morning-{date_tpe}"
            try:
                subprocess.check_call(cmd)
                out["sendEmailDidSend"] = True
                email_meta.update({
                    "ok": True,
                    "sentAtUtc": utc_now_iso(),
                    "subject": subj,
                    "durationMs": int((time.time() - t0) * 1000),
                    "lastError": None,
                })
                upsert_digest_delivery(
                    date_tpe=date_tpe,
                    channel="email",
                    target=str((payload.get("email") or {}).get("to") or ""),
                    status="sent",
                    batch_id=batch_id,
                    error=None,
                )
            except Exception as e:
                out["sendEmailDidSend"] = False
                err_s = f"{type(e).__name__}: {e}"
                email_meta.update({
                    "ok": False,
                    "sentAtUtc": None,
                    "subject": subj,
                    "durationMs": int((time.time() - t0) * 1000),
                    "lastError": err_s,
                })
                upsert_digest_delivery(
                    date_tpe=date_tpe,
                    channel="email",
                    target=str((payload.get("email") or {}).get("to") or ""),
                    status="failed",
                    batch_id=batch_id,
                    error=err_s,
                )

            # Write back payload status
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)

    out["ok"] = True
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
