#!/usr/bin/env python3
"""GeoSci RSS Fetcher (Step 3C): fetch + log per-feed, no item parsing yet.

- Selects feeds using the same ordering as geosci_select_feeds.py.
- Fetches up to N feeds (default 1 for Step 3C).
- Stores per-run + per-feed logs in SQLite.
- Updates feeds metadata (etag/last_modified/last_success_at_utc/etc.).

No external deps.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from rss.db import rss_store  # type: ignore

USER_AGENT = "OpenClaw GeoSci Fetcher/1.0"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def select_feeds(conn, limit: int) -> list[dict]:
    rows = conn.execute(
        """
        SELECT
          id, url, enabled, priority,
          etag, last_modified,
          last_success_at_utc, last_fetch_at_utc,
          consecutive_failures, next_fetch_after_utc,
          last_error
        FROM feeds
        WHERE enabled = 1
        ORDER BY
          CASE WHEN last_success_at_utc IS NULL THEN 0 ELSE 1 END ASC,
          CASE WHEN consecutive_failures > 0 THEN 0 ELSE 1 END ASC,
          CASE WHEN next_fetch_after_utc IS NULL THEN 0
               WHEN next_fetch_after_utc <= ? THEN 0
               ELSE 1 END ASC,
          priority DESC,
          COALESCE(next_fetch_after_utc, '') ASC,
          id ASC
        LIMIT ?
        """,
        (utc_now_iso(), int(limit)),
    ).fetchall()
    return [dict(r) for r in rows]


def fetch_url(url: str, *, etag: str | None, last_modified: str | None, timeout: int = 25) -> tuple[int, bytes, dict]:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
    }
    if etag:
        headers["If-None-Match"] = etag
    if last_modified:
        headers["If-Modified-Since"] = last_modified

    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = getattr(resp, "status", 200)
            data = resp.read()
            resp_headers = {k.lower(): v for k, v in resp.headers.items()}
            return int(status), data, resp_headers
    except urllib.error.HTTPError as e:
        # HTTPError is also a valid response; read body if present
        body = b""
        try:
            body = e.read() or b""
        except Exception:
            body = b""
        hdrs = {k.lower(): v for k, v in (e.headers.items() if e.headers else [])}
        return int(e.code), body, hdrs


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=1, help="Max feeds to fetch (Step 3C default 1)")
    ap.add_argument("--timeout", type=int, default=25)
    ap.add_argument("--kind", default="geosci")
    args = ap.parse_args()

    conn = rss_store.connect()
    rss_store.init_db(conn)

    run_id = rss_store.create_run(conn, kind=str(args.kind))
    run_started = utc_now_iso()

    feeds = select_feeds(conn, int(args.limit))

    results = []
    success = 0
    errors = 0

    for f in feeds:
        feed_id = int(f["id"])
        url = f["url"]
        started = utc_now_iso()
        t0 = time.time()

        status = None
        bytes_n = None
        ok = None
        err = None
        new_items_count = None  # not parsed yet

        try:
            status, data, hdrs = fetch_url(url, etag=f.get("etag"), last_modified=f.get("last_modified"), timeout=int(args.timeout))
            bytes_n = len(data)
            ok = 1 if (200 <= int(status) < 400 or int(status) == 304) else 0

            # Update feed metadata
            now = utc_now_iso()
            if ok:
                conn.execute(
                    """
                    UPDATE feeds
                    SET last_fetch_at_utc=?, last_success_at_utc=?, last_error=NULL,
                        consecutive_failures=0,
                        etag=COALESCE(?, etag),
                        last_modified=COALESCE(?, last_modified),
                        updated_at_utc=?
                    WHERE id=?
                    """,
                    (
                        now,
                        now,
                        hdrs.get("etag"),
                        hdrs.get("last-modified"),
                        now,
                        feed_id,
                    ),
                )
                success += 1
            else:
                raise RuntimeError(f"HTTP {status}")

        except Exception as e:
            ok = 0
            errors += 1
            err = f"{type(e).__name__}: {e}"
            now = utc_now_iso()
            conn.execute(
                """
                UPDATE feeds
                SET last_fetch_at_utc=?, last_error=?, consecutive_failures=consecutive_failures+1,
                    next_fetch_after_utc=?, updated_at_utc=?
                WHERE id=?
                """,
                (now, err, now, now, feed_id),
            )

        finished = utc_now_iso()

        rss_store.log_feed_fetch(
            conn,
            run_id=run_id,
            feed_id=feed_id,
            started_at_utc=started,
            finished_at_utc=finished,
            ok=bool(ok),
            http_status=int(status) if status is not None else None,
            bytes_n=int(bytes_n) if bytes_n is not None else None,
            new_items_count=new_items_count,
            error=err,
        )

        results.append(
            {
                "feedId": feed_id,
                "url": url,
                "ok": bool(ok),
                "httpStatus": status,
                "bytes": bytes_n,
                "durationMs": int((time.time() - t0) * 1000),
                "error": err,
            }
        )

    rss_store.finish_run(
        conn,
        run_id,
        ok=(errors == 0),
        feed_count=len(feeds),
        success_count=success,
        error_count=errors,
        notes="step3c:no-parse",
    )

    out = {
        "ok": errors == 0,
        "runId": run_id,
        "runStartedAtUtc": run_started,
        "kind": str(args.kind),
        "limit": int(args.limit),
        "results": results,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if errors == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
