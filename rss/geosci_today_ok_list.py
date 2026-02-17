#!/usr/bin/env python3
"""List today's GeoSci items (enrich_status='ok') for picking to portal.

- Select items by enriched_at_utc falling on today's date in Asia/Taipei.
- Output a compact, Telegram-friendly numbered list.

No external deps.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

DB_PATH = "/home/person/.openclaw/workspace/rss/db/geosci_rss.sqlite"


def taipei_today() -> str:
    return datetime.now(ZoneInfo("Asia/Taipei")).date().isoformat()


def clip(s: str, n: int) -> str:
    s = (s or "").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=80)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    date_tpe = taipei_today()

    rows = conn.execute(
        """
        SELECT
          i.id,
          COALESCE(f.title,f.url) AS journal,
          i.title,
          i.title_zh_tw,
          i.link,
          i.enriched_at_utc
        FROM items i
        JOIN feeds f ON f.id=i.feed_id
        WHERE i.enrich_status='ok'
          AND substr(datetime(i.enriched_at_utc, '+8 hours'), 1, 10) = ?
        ORDER BY i.enriched_at_utc DESC
        LIMIT ?
        """,
        (date_tpe, int(args.limit)),
    ).fetchall()

    items = [dict(r) for r in rows]

    if args.json:
        print(json.dumps({"ok": True, "dateTaipei": date_tpe, "count": len(items), "items": items}, ensure_ascii=False))
        return 0

    lines = [f"今日 GeoSci（{date_tpe}）可挑選清單：共 {len(items)} 篇", ""]
    for r in items:
        lines.append(f"[{r['id']}] {clip(r.get('title_zh_tw') or r.get('title') or '', 80)}")
        lines.append(f"    {clip(r.get('journal') or '', 60)}")
        lines.append(f"    {r.get('link') or ''}")
        lines.append("")

    print("\n".join(lines).rstrip() + "\n")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
