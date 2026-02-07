#!/usr/bin/env python3
"""Step 4D: Mark deliveries as sent for a batch.

- Finds pending/failed deliveries for channel/target.
- Marks up to N as sent with a batch_id.

This is intended to be called after a successful gist upload.

No external deps.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from rss.db import rss_store  # type: ignore


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--channel", default="geosci")
    ap.add_argument("--target", default="morning_digest")
    ap.add_argument("--batch-id", default=None)
    ap.add_argument("--gist-url", default=None)
    args = ap.parse_args()

    batch_id = args.batch_id or f"geosci-{utc_now_iso()}"

    conn = rss_store.connect()
    rss_store.init_db(conn)

    rows = rss_store.list_pending_items(conn, channel=str(args.channel), target=str(args.target), limit=int(args.limit))

    marked = 0
    for r in rows:
        delivery_id = int(r["delivery_id"])
        conn.execute(
            "UPDATE deliveries SET status='sent', sent_at_utc=?, batch_id=?, error=NULL WHERE id=?",
            (utc_now_iso(), batch_id, delivery_id),
        )
        marked += 1

    conn.commit()

    # Optional: write a note row into fetch_runs? (skip for now)

    remaining = conn.execute(
        "SELECT COUNT(*) FROM deliveries WHERE channel=? AND (target IS ? OR target=?) AND status IN ('pending','failed')",
        (str(args.channel), str(args.target), str(args.target)),
    ).fetchone()[0]

    out = {
        "ok": True,
        "batchId": batch_id,
        "gistUrl": args.gist_url,
        "markedSent": marked,
        "remainingPending": int(remaining),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
