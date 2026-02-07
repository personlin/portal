#!/usr/bin/env python3
"""Step B3: Translate title + abstract to zh-TW and write to SQLite.

Selects items where enrich_status='abstract_ok' and (title_zh_tw or abstract_zh_tw is null/empty).
Uses OpenAI Responses API via urllib (requires OPENAI_API_KEY).

Updates:
- title_zh_tw
- abstract_zh_tw
- enrich_status: translated_ok (if success), failed (if error)
- enrich_error
- enriched_at_utc

No external deps.
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
import time
import urllib.request
from datetime import datetime, timezone

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from rss.db import rss_store  # type: ignore

MODEL = os.environ.get("GEOSCI_TRANSLATE_MODEL", "gpt-4o-mini")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def openai_translate(title: str, abstract: str) -> tuple[str, str]:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY not set")

    prompt = (
        "你是專業科學編輯。請將以下英語內容翻譯成繁體中文（台灣用語），保持術語一致、語氣精準。\n"
        "要求：\n"
        "- 只輸出 JSON，格式：{\"title_zh_tw\":..., \"abstract_zh_tw\":...}\n"
        "- 不要加入任何多餘文字。\n\n"
        f"TITLE: {title}\n\nABSTRACT: {abstract}"
    )

    payload = {
        "model": MODEL,
        "input": prompt,
        "text": {"format": {"type": "json_object"}},
    }

    req = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    raw = urllib.request.urlopen(req, timeout=90).read().decode("utf-8", errors="ignore")
    data = json.loads(raw)

    # responses API returns output_text in convenience fields sometimes; fall back to walking.
    txt = data.get("output_text")
    if not txt:
        # Walk output
        parts = []
        for o in data.get("output", []) or []:
            for c in (o.get("content") or []):
                if c.get("type") == "output_text" and c.get("text"):
                    parts.append(c["text"])
        txt = "\n".join(parts).strip()

    obj = json.loads(txt)
    t = (obj.get("title_zh_tw") or "").strip()
    a = (obj.get("abstract_zh_tw") or "").strip()
    if not t or not a:
        raise RuntimeError("translation_empty")
    return t, a


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=3)
    ap.add_argument("--sleep", type=float, default=0.0)
    args = ap.parse_args()

    conn = rss_store.connect()
    rss_store.init_db(conn)

    rows = conn.execute(
        """
        SELECT id, title, abstract
        FROM items
        WHERE enrich_status='abstract_ok'
          AND (title_zh_tw IS NULL OR title_zh_tw=''
               OR abstract_zh_tw IS NULL OR abstract_zh_tw='')
        ORDER BY first_seen_at_utc ASC
        LIMIT ?
        """,
        (int(args.limit),),
    ).fetchall()

    results = []
    for (item_id, title, abstract) in rows:
        started = time.time()
        try:
            t_zh, a_zh = openai_translate(title or "", abstract or "")
            conn.execute(
                """
                UPDATE items
                SET title_zh_tw=?, abstract_zh_tw=?,
                    enrich_status='translated_ok', enrich_error=NULL, enriched_at_utc=?
                WHERE id=?
                """,
                (t_zh, a_zh, utc_now_iso(), int(item_id)),
            )
            conn.commit()
            results.append({"itemId": int(item_id), "ok": True, "titleZhLen": len(t_zh), "absZhLen": len(a_zh), "durationMs": int((time.time()-started)*1000)})
        except Exception as e:
            err = f"{type(e).__name__}: {e}"
            conn.execute(
                "UPDATE items SET enrich_status='failed', enrich_error=?, enriched_at_utc=? WHERE id=?",
                (err, utc_now_iso(), int(item_id)),
            )
            conn.commit()
            results.append({"itemId": int(item_id), "ok": False, "error": err, "durationMs": int((time.time()-started)*1000)})

        if args.sleep:
            time.sleep(float(args.sleep))

    out = {"ok": True, "count": len(rows), "model": MODEL, "results": results}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
