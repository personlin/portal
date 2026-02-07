#!/usr/bin/env python3
"""Step 4F-2: GeoSci catch-up helper.

If DB has pending/failed deliveries for (channel=geosci, target=morning_digest),
run geosci_db_to_gist to produce a gist and mark those items sent.

Does NOT send Telegram/Email and does NOT touch morning outbox.

Outputs JSON.
"""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
from datetime import datetime
from zoneinfo import ZoneInfo

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "db", "geosci_rss.sqlite")
GEOSCI_DB_TO_GIST = os.path.join(BASE_DIR, "geosci_db_to_gist.py")


def taipei_date() -> str:
    return datetime.now(ZoneInfo("Asia/Taipei")).date().isoformat()


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=120)
    ap.add_argument("--channel", default="geosci")
    ap.add_argument("--target", default="morning_digest")
    args = ap.parse_args()

    if not os.path.exists(DB_PATH):
        print(json.dumps({"ok": False, "error": "db_missing", "dbPath": DB_PATH}, ensure_ascii=False))
        return 2

    conn = sqlite3.connect(DB_PATH)
    pending = conn.execute(
        "SELECT COUNT(*) FROM deliveries WHERE channel=? AND target=? AND status IN ('pending','failed')",
        (str(args.channel), str(args.target)),
    ).fetchone()[0]

    if int(pending) <= 0:
        print(json.dumps({"ok": True, "dateTaipei": taipei_date(), "pending": 0, "didRun": False}, ensure_ascii=False, indent=2))
        return 0

    # Run DB->gist
    raw = subprocess.check_output(
        ["python3", GEOSCI_DB_TO_GIST, "--limit", str(int(args.limit))],
        text=True,
    )
    data = json.loads(raw)

    out = {
        "ok": bool(data.get("ok")),
        "dateTaipei": taipei_date(),
        "pendingBefore": int(pending),
        "didRun": True,
        "result": data,
    }

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
