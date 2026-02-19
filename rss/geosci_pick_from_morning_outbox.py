#!/usr/bin/env python3
"""Build portal pick list based on the SAME set as the morning digest.

Reads morning outbox JSON (morning-YYYY-MM-DD.json) to find the GeoSci batchId,
then queries SQLite deliveries/items for that batch.

This makes the noon pick list consistent with the morning digest.

No external deps.
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

DB_PATH = "/home/person/.openclaw/workspace/rss/db/geosci_rss.sqlite"
OUTBOX_DIR = "/home/person/.openclaw/workspace/rss/outbox"


def taipei_date() -> str:
    return datetime.now(ZoneInfo("Asia/Taipei")).date().isoformat()


def clip(s: str, n: int) -> str:
    s = (s or "").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None, help="Taipei date YYYY-MM-DD (default today)")
    ap.add_argument("--limit", type=int, default=30)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    date_tpe = args.date or taipei_date()
    outbox_path = os.path.join(OUTBOX_DIR, f"morning-{date_tpe}.json")

    if not os.path.exists(outbox_path):
        print(json.dumps({"ok": False, "error": "missing_outbox", "dateTaipei": date_tpe, "outbox": outbox_path}, ensure_ascii=False))
        return 2

    outbox = json.load(open(outbox_path, "r", encoding="utf-8"))
    geosci = (outbox.get("geosci") or {})
    batch_id = geosci.get("batchId")
    gist_url = geosci.get("gistUrl")

    if not batch_id:
        print(json.dumps({"ok": False, "error": "missing_geosci_batchId", "dateTaipei": date_tpe, "outbox": outbox_path}, ensure_ascii=False))
        return 2

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        """
        SELECT
          i.id,
          COALESCE(f.title,f.url) AS journal,
          i.title,
          i.title_zh_tw,
          i.link,
          i.summary_zh_tw,
          d.batch_id,
          d.sent_at_utc
        FROM deliveries d
        JOIN items i ON i.id=d.item_id
        JOIN feeds f ON f.id=i.feed_id
        WHERE d.channel='geosci' AND d.target='morning_digest'
          AND d.batch_id=?
        ORDER BY d.id ASC
        LIMIT ?
        """,
        (str(batch_id), int(args.limit)),
    ).fetchall()

    items = [dict(r) for r in rows]

    if args.json:
        print(
            json.dumps(
                {
                    "ok": True,
                    "dateTaipei": date_tpe,
                    "batchId": batch_id,
                    "gistUrl": gist_url,
                    "count": len(items),
                    "items": items,
                },
                ensure_ascii=False,
            )
        )
        return 0

    lines = [f"今日 GeoSci 可挑選清單（{date_tpe}；同早安彙整）：共 {len(items)} 篇", ""]
    for r in items:
        lines.append(f"[{r['id']}] {clip(r.get('title_zh_tw') or r.get('title') or '', 80)}")
        lines.append(f"    {clip(r.get('journal') or '', 60)}")
        lines.append("")

    if gist_url:
        lines.append(f"（早安彙整 Gist：{gist_url}）")

    print("\n".join(lines).rstrip() + "\n")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
