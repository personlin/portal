#!/usr/bin/env python3
"""Queue deliveries for complete (enrich_status='ok') items.

Rationale:
- Existing pipeline marks deliveries sent when gist is created.
- If we switch digest to only include ok items, we need a way to (re)queue ok items
  that were previously sent while incomplete.

This script creates (or resets) deliveries to pending for items with enrich_status='ok'.

Default behavior:
- For any matching delivery rows (channel/target) currently status='sent' or 'failed', set to 'pending'.
- For ok items missing a delivery row, insert pending.

No external deps.
"""

from __future__ import annotations

import json
import os
import sys

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from rss.db import rss_store  # type: ignore


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--channel", default="geosci")
    ap.add_argument("--target", default="morning_digest")
    ap.add_argument("--limit", type=int, default=200)
    args = ap.parse_args()

    conn = rss_store.connect()
    rss_store.init_db(conn)

    # 1) Reset existing deliveries to pending for ok items
    # limit by oldest first_seen
    ids = [
        r[0]
        for r in conn.execute(
            """
            SELECT i.id
            FROM items i
            WHERE i.enrich_status='ok'
            ORDER BY i.first_seen_at_utc ASC
            LIMIT ?
            """,
            (int(args.limit),),
        ).fetchall()
    ]

    if not ids:
        print(json.dumps({"ok": True, "queued": 0, "note": "no ok items"}, ensure_ascii=False, indent=2))
        return 0

    q_marks = 0
    for item_id in ids:
        row = conn.execute(
            "SELECT id, status FROM deliveries WHERE item_id=? AND channel=? AND target=? ORDER BY id DESC LIMIT 1",
            (int(item_id), str(args.channel), str(args.target)),
        ).fetchone()
        if row:
            delivery_id, status = int(row[0]), row[1]
            if status != 'pending':
                conn.execute(
                    "UPDATE deliveries SET status='pending', error=NULL WHERE id=?",
                    (delivery_id,),
                )
                q_marks += 1
        else:
            conn.execute(
                "INSERT INTO deliveries(item_id, channel, target, status, created_at_utc) VALUES (?,?,?,?,?)",
                (int(item_id), str(args.channel), str(args.target), 'pending', rss_store.utc_now_iso()),
            )
            q_marks += 1

    conn.commit()

    pending = conn.execute(
        "SELECT COUNT(*) FROM deliveries WHERE channel=? AND target=? AND status='pending'",
        (str(args.channel), str(args.target)),
    ).fetchone()[0]

    print(json.dumps({"ok": True, "considered": len(ids), "queued": q_marks, "pendingNow": int(pending)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
