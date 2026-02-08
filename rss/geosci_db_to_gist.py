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
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

# allow importing rss.db when run as a script
WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from rss.db import rss_store  # type: ignore

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


def record_batch(*, kind: str, date_tpe: str, batch_id: str, status: str, gist_url: str | None, gist_id: str | None,
                 included_count: int, remaining_pending_after: int | None, error: str | None) -> None:
    conn = rss_store.connect()
    rss_store.init_db(conn)
    conn.execute(
        """
        INSERT INTO digest_batches(
          kind, date_taipei, batch_id, gist_url, gist_id, included_count,
          remaining_pending_after, status, error, created_at_utc
        ) VALUES (?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(batch_id) DO UPDATE SET
          gist_url=excluded.gist_url,
          gist_id=excluded.gist_id,
          included_count=excluded.included_count,
          remaining_pending_after=excluded.remaining_pending_after,
          status=excluded.status,
          error=excluded.error
        """,
        (
            kind,
            date_tpe,
            batch_id,
            gist_url,
            gist_id,
            int(included_count),
            remaining_pending_after,
            status,
            error,
            rss_store.utc_now_iso(),
        ),
    )
    conn.commit()


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=120, help="Max pending items to include in one gist")
    ap.add_argument("--channel", default="geosci")
    ap.add_argument("--target", default="morning_digest")
    ap.add_argument("--description", default=None)
    ap.add_argument("--include-sent", action="store_true", help="Preview: include recently sent items (does NOT mark deliveries)")
    ap.add_argument("--only-ok", action="store_true", help="Only include items with enrich_status='ok' (complete fields)")
    args = ap.parse_args()

    date_tpe = taipei_date()
    out_md = f"/tmp/geosci-db-{date_tpe}.md"

    desc = args.description or f"GeoSci RSS Digest (DB) {date_tpe}"

    # 1) Build markdown
    md_cmd = [
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
    ]
    if args.include_sent:
        md_cmd.append("--include-sent")
    if args.only_ok:
        md_cmd.append("--only-ok")
    md = run_json(md_cmd)

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
        # Record failed batch (no batch_id yet; create a stable one)
        batch_id = f"geosci-{rss_store.utc_now_iso()}"
        record_batch(
            kind="geosci",
            date_tpe=date_tpe,
            batch_id=batch_id,
            status="failed",
            gist_url=None,
            gist_id=None,
            included_count=int(md.get("count") or 0),
            remaining_pending_after=None,
            error="gist_upload_failed",
        )
        print(json.dumps({"ok": False, "stage": "gist_upload", "md": md, "gist": gist, "batchId": batch_id}, ensure_ascii=False, indent=2))
        return 2

    gist_url = gist.get("url")
    gist_id = gist.get("id")

    if args.include_sent:
        # Preview mode: do NOT mark delivered / do NOT record as a batch.
        out = {
            "ok": True,
            "dateTaipei": date_tpe,
            "includedCount": int(md.get("count") or 0),
            "mdPath": md.get("outPath"),
            "gistUrl": gist_url,
            "gistId": gist_id,
            "batchId": f"preview-{rss_store.utc_now_iso()}",
            "markedSent": 0,
            "remainingPending": None,
            "preview": True,
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

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

    batch_id = marked.get("batchId")

    # 4) Record batch in DB
    record_batch(
        kind="geosci",
        date_tpe=date_tpe,
        batch_id=str(batch_id),
        status="created",
        gist_url=str(gist_url),
        gist_id=str(gist_id) if gist_id else None,
        included_count=int(md.get("count") or 0),
        remaining_pending_after=int(marked.get("remainingPending")) if marked.get("remainingPending") is not None else None,
        error=None,
    )

    out = {
        "ok": True,
        "dateTaipei": date_tpe,
        "includedCount": int(md.get("count") or 0),
        "mdPath": md.get("outPath"),
        "gistUrl": gist_url,
        "gistId": gist_id,
        "batchId": batch_id,
        "markedSent": marked.get("markedSent"),
        "remainingPending": marked.get("remainingPending"),
    }

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
