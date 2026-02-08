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
    ap.add_argument("--min-journals", type=int, default=5, help="Try to queue at least this many distinct journals")
    args = ap.parse_args()

    conn = rss_store.connect()
    rss_store.init_db(conn)

    # 1) Select ok items, but queue them in a journal-diverse way.
    pool_limit = max(int(args.limit) * 10, 400)
    pool = conn.execute(
        """
        SELECT i.id, COALESCE(f.title,f.url) AS journal, i.first_seen_at_utc
        FROM items i
        JOIN feeds f ON f.id = i.feed_id
        WHERE i.enrich_status='ok'
        ORDER BY i.first_seen_at_utc ASC
        LIMIT ?
        """,
        (int(pool_limit),),
    ).fetchall()

    by_j = {}
    for item_id, journal, _fs in pool:
        by_j.setdefault(journal, []).append(int(item_id))

    journals = list(by_j.keys())
    # journals already ordered by earliest first_seen due to SELECT ordering + append order

    target_j = max(1, int(args.min_journals))

    picked: list[int] = []
    distinct = 0

    # First pass: take one from as many journals as possible (up to min-journals)
    for j in journals:
        if len(picked) >= int(args.limit):
            break
        if distinct >= target_j:
            break
        if by_j.get(j):
            picked.append(by_j[j].pop(0))
            distinct += 1

    # Round-robin fill until limit
    idx = 0
    active = [j for j in journals if by_j.get(j)]
    while len(picked) < int(args.limit) and active:
        j = active[idx % len(active)]
        picked.append(by_j[j].pop(0))
        active = [jj for jj in active if by_j.get(jj)]
        idx += 1
        if idx > 10000:
            break

    ids = picked

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
                    "UPDATE deliveries SET status='pending', error=NULL, created_at_utc=? WHERE id=?",
                    (rss_store.utc_now_iso(), delivery_id),
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
