#!/usr/bin/env python3
"""Step 4B: Build a GeoSci digest markdown from SQLite pending items.

- Reads pending/failed deliveries for channel=geosci, target=morning_digest.
- Writes markdown to /tmp/geosci-db-YYYY-MM-DD.md (Asia/Taipei date).
- Does NOT upload gist, does NOT mark sent.

No external deps.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from rss.db import rss_store  # type: ignore


def taipei_date() -> str:
    return datetime.now(ZoneInfo("Asia/Taipei")).date().isoformat()


def md_escape(s: str) -> str:
    return (s or "").replace("\r", " ").strip()


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=300)
    ap.add_argument("--channel", default="geosci")
    ap.add_argument("--target", default="morning_digest")
    ap.add_argument("--out", default=None)
    ap.add_argument("--include-sent", action="store_true", help="Preview recently sent items (for formatting checks)")
    args = ap.parse_args()

    conn = rss_store.connect()
    rss_store.init_db(conn)

    if args.include_sent:
        rows = conn.execute(
            """
            SELECT i.*, f.url AS feed_url, COALESCE(f.title,f.url) AS feed_title, d.id AS delivery_id, d.status AS delivery_status
            FROM deliveries d
            JOIN items i ON i.id = d.item_id
            JOIN feeds f ON f.id = i.feed_id
            WHERE d.channel = ? AND d.target = ? AND d.status = 'sent'
            ORDER BY d.sent_at_utc DESC
            LIMIT ?
            """,
            (str(args.channel), str(args.target), int(args.limit)),
        ).fetchall()
    else:
        rows = rss_store.list_pending_items(conn, channel=str(args.channel), target=str(args.target), limit=int(args.limit))
    date_tpe = taipei_date()
    out_path = args.out or f"/tmp/geosci-db-{date_tpe}.md"

    title = f"GeoSci Journals Digest (DB pending) — {date_tpe}"

    lines = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"GeneratedAt (UTC): {rss_store.utc_now_iso()}")
    lines.append(f"Channel: {args.channel} | Target: {args.target}")
    lines.append("")
    lines.append(f"Pending items in this file: {len(rows)}")
    lines.append("")

    if not rows:
        lines.append("## No pending items")
    else:
        # Group by feed (use human-friendly journal/feed title)
        by_feed: dict[str, list] = {}
        for r in rows:
            key = r["feed_title"] or r["feed_url"]
            by_feed.setdefault(key, []).append(r)

        def clip(s: str, n: int) -> str:
            s = (s or "").strip()
            return s if len(s) <= n else (s[: n - 1] + "…")

        for feed_title in sorted(by_feed.keys()):
            items = by_feed[feed_title]
            lines.append(f"## {md_escape(feed_title)} ({len(items)})")
            lines.append("")

            for r in items:
                title_en = md_escape(r["title"] or "(no title)")
                title_zh = md_escape(((r["title_zh_tw"] if "title_zh_tw" in r.keys() else None) or "").strip())
                if not title_zh:
                    title_zh = "（pending enrichment：繁中標題）"

                link = (r["link"] or "").strip()
                pub = (r["published_at"] or "").strip()
                doi = ((r["doi"] if "doi" in r.keys() else None) or "").strip()

                abs_en = ((r["abstract"] if "abstract" in r.keys() else None) or "").strip()
                abs_zh = ((r["abstract_zh_tw"] if "abstract_zh_tw" in r.keys() else None) or "").strip()
                sum_en = ((r["summary_en"] if "summary_en" in r.keys() else None) or "").strip()
                sum_zh = ((r["summary_zh_tw"] if "summary_zh_tw" in r.keys() else None) or "").strip()

                # 1) Titles
                lines.append(f"### {title_en}")
                lines.append(f"### {title_zh}")
                lines.append("")

                # 2) Metadata
                if link:
                    lines.append(f"- Link: {link}")
                if pub:
                    lines.append(f"- Published: {pub}")
                if doi:
                    lines.append(f"- DOI: {doi}")
                lines.append("")

                # 3) Abstracts (bounded)
                lines.append("**Abstract (EN)**")
                lines.append("")
                lines.append(clip(abs_en, 2000) if abs_en else "（pending enrichment：Abstract EN）")
                lines.append("")

                lines.append("**Abstract (zh-TW)**")
                lines.append("")
                lines.append(clip(abs_zh, 2000) if abs_zh else "（pending enrichment：Abstract zh-TW）")
                lines.append("")

                # 4) Summaries (bounded)
                lines.append("**Summary (EN)**")
                lines.append("")
                lines.append(clip(sum_en, 600) if sum_en else "（pending enrichment：Summary EN）")
                lines.append("")

                lines.append("**Summary (zh-TW)**")
                lines.append("")
                lines.append(clip(sum_zh, 600) if sum_zh else "（pending enrichment：Summary zh-TW）")
                lines.append("")

                lines.append("---")
                lines.append("")

    content = "\n".join(lines)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)

    out = {
        "ok": True,
        "outPath": out_path,
        "dateTaipei": date_tpe,
        "count": len(rows),
        "bytes": len(content.encode("utf-8")),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
