#!/usr/bin/env python3
"""Step 4E-1: GeoSci DB -> markdown -> secret gist -> mark deliveries sent.

This script is the bridge between the SQLite queue and the morning digest.

Flow:
1) Build markdown from DB pending items (geosci_db_to_md.py)
2) Upload secret gist (gist_upload.py)
3) Mark delivered in DB (geosci_mark_delivered.py)

Outputs JSON.

No external deps.
"""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime
from zoneinfo import ZoneInfo

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(BASE_DIR)

DB_TO_MD = os.path.join(BASE_DIR, "geosci_db_to_md.py")
GIST_UPLOAD = os.path.join(BASE_DIR, "gist_upload.py")
MARK_DELIVERED = os.path.join(BASE_DIR, "geosci_mark_delivered.py")


def taipei_date() -> str:
    return datetime.now(ZoneInfo("Asia/Taipei")).date().isoformat()


def run_json(cmd: list[str]) -> dict:
    out = subprocess.check_output(cmd, text=True)
    return json.loads(out)


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=120, help="Max pending items to include in one gist")
    ap.add_argument("--channel", default="geosci")
    ap.add_argument("--target", default="morning_digest")
    ap.add_argument("--description", default=None)
    args = ap.parse_args()

    date_tpe = taipei_date()
    out_md = f"/tmp/geosci-db-{date_tpe}.md"

    desc = args.description or f"GeoSci RSS Digest (DB) {date_tpe}"

    # 1) Build markdown
    md = run_json([
        "python3",
        DB_TO_MD,
        "--limit",
        str(int(args.limit)),
        "--channel",
        str(args.channel),
        "--target",
        str(args.target),
        "--out",
        out_md,
    ])

    # 2) Upload gist
    gist = run_json([
        "python3",
        GIST_UPLOAD,
        "--file",
        out_md,
        "--description",
        desc,
    ])

    if not gist.get("ok"):
        print(json.dumps({"ok": False, "stage": "gist_upload", "md": md, "gist": gist}, ensure_ascii=False, indent=2))
        return 2

    gist_url = gist.get("url")

    # 3) Mark delivered (sent)
    marked = run_json([
        "python3",
        MARK_DELIVERED,
        "--limit",
        str(int(md.get("count") or 0)),
        "--channel",
        str(args.channel),
        "--target",
        str(args.target),
        "--gist-url",
        str(gist_url),
    ])

    out = {
        "ok": True,
        "dateTaipei": date_tpe,
        "includedCount": int(md.get("count") or 0),
        "mdPath": md.get("outPath"),
        "gistUrl": gist_url,
        "gistId": gist.get("id"),
        "batchId": marked.get("batchId"),
        "markedSent": marked.get("markedSent"),
        "remainingPending": marked.get("remainingPending"),
    }

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
