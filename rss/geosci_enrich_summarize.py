#!/usr/bin/env python3
"""Step B4: Summarize abstract into EN + zh-TW and write to SQLite.

Selects items where enrich_status='translated_ok' and summaries are missing.
Uses OpenAI Responses API. Default model: gpt-4o-mini.

Updates:
- summary_en (2–4 sentences)
- summary_zh_tw (2–4 sentences)
- enrich_status: summarized_ok
- enrich_error/enriched_at_utc

No external deps.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from rss.db import rss_store  # type: ignore

MODEL = os.environ.get("GEOSCI_SUMMARY_MODEL", "gpt-4o-mini")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def openai_summarize(title: str, abstract: str) -> tuple[str, str]:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY not set")

    prompt = (
        "You are a scientific editor. Summarize the following paper abstract.\n"
        "Requirements:\n"
        "- Output ONLY JSON: {\"summary_en\":..., \"summary_zh_tw\":...}\n"
        "- summary_en: 2-4 sentences, plain English.\n"
        "- summary_zh_tw: 2-4 sentences, Traditional Chinese (Taiwan).\n"
        "- Do not add citations or fabricate results not in abstract.\n\n"
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

    parts = []
    for o in data.get("output", []) or []:
        for c in (o.get("content") or []):
            if c.get("type") == "output_text" and c.get("text"):
                parts.append(c["text"])
    txt = "\n".join(parts).strip()

    obj = json.loads(txt)
    s_en = (obj.get("summary_en") or "").strip()
    s_zh = (obj.get("summary_zh_tw") or "").strip()
    if not s_en or not s_zh:
        raise RuntimeError("summary_empty")
    return s_en, s_zh


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
        WHERE enrich_status='translated_ok'
          AND (summary_en IS NULL OR summary_en='' OR summary_zh_tw IS NULL OR summary_zh_tw='')
        ORDER BY first_seen_at_utc ASC
        LIMIT ?
        """,
        (int(args.limit),),
    ).fetchall()

    results = []
    for (item_id, title, abstract) in rows:
        started = time.time()
        try:
            s_en, s_zh = openai_summarize(title or "", abstract or "")
            conn.execute(
                """
                UPDATE items
                SET summary_en=?, summary_zh_tw=?,
                    enrich_status='summarized_ok', enrich_error=NULL, enriched_at_utc=?
                WHERE id=?
                """,
                (s_en, s_zh, utc_now_iso(), int(item_id)),
            )
            conn.commit()
            results.append({"itemId": int(item_id), "ok": True, "enLen": len(s_en), "zhLen": len(s_zh), "durationMs": int((time.time()-started)*1000)})
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
