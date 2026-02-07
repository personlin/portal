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
    args = ap.parse_args()

    conn = rss_store.connect()
    rss_store.init_db(conn)

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
        # Group by feed
        by_feed: dict[str, list] = {}
        for r in rows:
            key = r["feed_title"] or r["feed_url"]
            by_feed.setdefault(key, []).append(r)

        for feed_title in sorted(by_feed.keys()):
            items = by_feed[feed_title]
            lines.append(f"## {md_escape(feed_title)} ({len(items)})")
            lines.append("")
            for r in items:
                t = md_escape(r["title"] or "(no title)")
                link = (r["link"] or "").strip()
                pub = (r["published_at"] or "").strip()
                doi = (r["doi"] or "").strip() if "doi" in r.keys() else ""

                lines.append(f"### {t}")
                if link:
                    lines.append(f"- Link: {link}")
                if pub:
                    lines.append(f"- Published: {pub}")
                if doi:
                    lines.append(f"- DOI: {doi}")

                abs_txt = (r["abstract"] or "").strip() if "abstract" in r.keys() else ""
                if abs_txt:
                    lines.append("")
                    lines.append("**Abstract**")
                    lines.append("")
                    # keep it bounded for now
                    if len(abs_txt) > 2500:
                        abs_txt = abs_txt[:2499] + "…"
                    lines.append(abs_txt)

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
