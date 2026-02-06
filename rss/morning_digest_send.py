#!/usr/bin/env python3
"""Send the morning digest from the persisted outbox payload.

Step 2C-1: read + validate only (no sending yet).

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
from datetime import datetime
from zoneinfo import ZoneInfo

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTBOX_DIR = os.path.join(BASE_DIR, "outbox")


def taipei_date() -> str:
    return datetime.now(ZoneInfo("Asia/Taipei")).date().isoformat()


def paths(date_tpe: str) -> tuple[str, str, str]:
    base = os.path.join(OUTBOX_DIR, f"morning-{date_tpe}")
    return base + ".json", base + ".email.txt", base + ".email.html"


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def main() -> int:
    date_tpe = taipei_date()
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

    # Prefer sidecar files if present
    email_text = read_text(txt_path) if os.path.exists(txt_path) else (payload.get("email") or {}).get("text") or ""
    email_html = read_text(html_path) if os.path.exists(html_path) else (payload.get("email") or {}).get("html") or ""

    out["email"] = {
        "to": (payload.get("email") or {}).get("to"),
        "from": (payload.get("email") or {}).get("from"),
        "subject": (payload.get("email") or {}).get("subject"),
        "textLen": len(email_text or ""),
        "htmlLen": len(email_html or ""),
    }

    tg_text = (payload.get("telegram") or {}).get("text") or ""
    out["telegram"] = {"textLen": len(tg_text)}

    out["ok"] = True
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
