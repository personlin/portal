#!/usr/bin/env python3
"""Step 1: Build a pick-list from queued GeoSci items.

Reads SQLite and lists items that are queued to be sent (deliveries.pending)
AND have enrich_status='ok' (complete fields).

Outputs either:
- plain text (default)
- markdown (--md)

No external deps.
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

DB_PATH = "/home/person/.openclaw/workspace/rss/db/geosci_rss.sqlite"


def taipei_date() -> str:
    return datetime.now(ZoneInfo("Asia/Taipei")).date().isoformat()


def clip(s: str, n: int) -> str:
    s = (s or "").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--min-journals", type=int, default=1, help="Try to include at least this many distinct journals")
    ap.add_argument("--channel", default="geosci")
    ap.add_argument("--target", default="morning_digest")
    ap.add_argument("--md", action="store_true")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Fetch a larger pool, then pick in a journal-diverse way.
    pool_limit = max(int(args.limit) * 8, 200)
    pool = conn.execute(
        """
        SELECT
          i.id,
          COALESCE(f.title,f.url) AS journal,
          i.title,
          i.title_zh_tw,
          i.link,
          i.summary_zh_tw,
          i.enriched_at_utc,
          d.created_at_utc
        FROM deliveries d
        JOIN items i ON i.id = d.item_id
        JOIN feeds f ON f.id = i.feed_id
        WHERE d.channel=? AND d.target=? AND d.status='pending'
          AND i.enrich_status='ok'
        ORDER BY d.created_at_utc ASC
        LIMIT ?
        """,
        (str(args.channel), str(args.target), int(pool_limit)),
    ).fetchall()

    # Group by journal then round-robin pick.
    by_j = {}
    for r in pool:
        by_j.setdefault(r["journal"], []).append(r)

    journals = list(by_j.keys())
    # If not enough distinct journals, just use what's available.
    # Otherwise, prioritize the earliest items from as many journals as possible.
    # Sort journals by their earliest created_at_utc.
    journals.sort(key=lambda j: by_j[j][0]["created_at_utc"])

    picked = []
    j_count_target = max(1, int(args.min_journals))

    # First pass: take 1 from each journal until we hit min-journals or limit.
    for j in journals:
        if len(picked) >= int(args.limit):
            break
        if len(set([x["journal"] for x in picked])) >= j_count_target:
            break
        picked.append(by_j[j].pop(0))

    # Round-robin: keep cycling journals adding one each time.
    idx = 0
    while len(picked) < int(args.limit) and journals:
        j = journals[idx % len(journals)]
        if by_j.get(j):
            picked.append(by_j[j].pop(0))
        # remove empty journals
        journals = [jj for jj in journals if by_j.get(jj)]
        idx += 1
        if idx > 5000:
            break

    rows = picked

    date_tpe = taipei_date()

    if args.md:
        lines = [f"# 今日可挑選清單（{date_tpe}）", "", f"共 {len(rows)} 篇（顯示前 {int(args.limit)} 篇）", ""]
        for r in rows:
            lines.append(f"## [{r['id']}] {r['title_zh_tw']}")
            lines.append(f"**{r['title']}**")
            lines.append("")
            lines.append(f"- 期刊：{r['journal']}")
            lines.append(f"- Link：{r['link']}")
            lines.append(f"- 摘要：{clip(r['summary_zh_tw'] or '', 220) or '（無）'}")
            lines.append("")
        out_text = "\n".join(lines)
    else:
        lines = [f"今日可挑選清單（{date_tpe}）— 前 {int(args.limit)} 篇", ""]
        for r in rows:
            lines.append(f"[{r['id']}] {clip(r['title_zh_tw'], 80)}")
            lines.append(f"    {clip(r['title'], 90)}")
            lines.append(f"    期刊：{clip(r['journal'], 60)}")
            lines.append(f"    Link：{r['link']}")
            lines.append(f"    摘要：{clip(r['summary_zh_tw'] or '', 160) or '（無）'}")
            lines.append("")
        out_text = "\n".join(lines).rstrip() + "\n"

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(out_text)
        print(json.dumps({"ok": True, "count": len(rows), "out": args.out}, ensure_ascii=False, indent=2))
    else:
        print(out_text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
