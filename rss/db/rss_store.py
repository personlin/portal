#!/usr/bin/env python3
"""SQLite store for GeoSci RSS reliability.

Step 2: schema + minimal CRUD helpers (no fetching yet).

DB path:
- /home/person/.openclaw/workspace/rss/db/geosci_rss.sqlite

No external deps.
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "geosci_rss.sqlite")
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.sql")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def connect(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    # WAL + FK safety
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def _ensure_columns(conn: sqlite3.Connection, table: str, cols: list[tuple[str, str]]) -> None:
    existing = {r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    for name, decl in cols:
        if name in existing:
            continue
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {decl}")


def init_db(conn: sqlite3.Connection) -> None:
    if not os.path.exists(SCHEMA_PATH):
        raise FileNotFoundError(SCHEMA_PATH)
    schema = open(SCHEMA_PATH, "r", encoding="utf-8").read()
    conn.executescript(schema)

    # Migrations (safe ALTER for existing DBs)
    _ensure_columns(conn, "items", [
        ("title_zh_tw", "TEXT"),
        ("abstract_zh_tw", "TEXT"),
        ("summary_en", "TEXT"),
        ("summary_zh_tw", "TEXT"),
        ("enrich_status", "TEXT"),
        ("enrich_error", "TEXT"),
        ("enriched_at_utc", "TEXT"),
    ])

    conn.commit()


def ensure_feed(conn: sqlite3.Connection, url: str, *, title: str | None = None, category: str | None = None, publisher: str | None = None) -> int:
    now = utc_now_iso()
    cur = conn.execute("SELECT id FROM feeds WHERE url=?", (url,))
    row = cur.fetchone()
    if row:
        conn.execute(
            "UPDATE feeds SET title=COALESCE(?, title), category=COALESCE(?, category), publisher=COALESCE(?, publisher), updated_at_utc=? WHERE id=?",
            (title, category, publisher, now, int(row["id"])),
        )
        conn.commit()
        return int(row["id"])

    conn.execute(
        "INSERT INTO feeds(url,title,publisher,category,created_at_utc,updated_at_utc) VALUES (?,?,?,?,?,?)",
        (url, title, publisher, category, now, now),
    )
    conn.commit()
    return int(conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"])


def create_run(conn: sqlite3.Connection, *, kind: str = "geosci") -> int:
    now = utc_now_iso()
    conn.execute(
        "INSERT INTO fetch_runs(kind, started_at_utc) VALUES (?, ?)",
        (kind, now),
    )
    conn.commit()
    return int(conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"])


def finish_run(conn: sqlite3.Connection, run_id: int, *, ok: bool, feed_count: int, success_count: int, error_count: int, notes: str | None = None) -> None:
    conn.execute(
        "UPDATE fetch_runs SET finished_at_utc=?, ok=?, feed_count=?, success_count=?, error_count=?, notes=? WHERE id=?",
        (utc_now_iso(), 1 if ok else 0, feed_count, success_count, error_count, notes, run_id),
    )
    conn.commit()


def log_feed_fetch(conn: sqlite3.Connection, *, run_id: int, feed_id: int, started_at_utc: str, finished_at_utc: str | None, ok: bool | None,
                  http_status: int | None, bytes_n: int | None, new_items_count: int | None, error: str | None) -> None:
    conn.execute(
        "INSERT INTO feed_fetch_logs(run_id, feed_id, started_at_utc, finished_at_utc, ok, http_status, bytes, new_items_count, error) VALUES (?,?,?,?,?,?,?,?,?)",
        (
            run_id,
            feed_id,
            started_at_utc,
            finished_at_utc,
            None if ok is None else (1 if ok else 0),
            http_status,
            bytes_n,
            new_items_count,
            error,
        ),
    )
    conn.commit()


def upsert_item(conn: sqlite3.Connection, *, feed_id: int, dedup_hash: str, entry: dict) -> tuple[int, bool]:
    """Insert item if new; else update last_seen_at_utc.

    Returns (item_id, inserted_new).
    """
    now = utc_now_iso()
    cur = conn.execute("SELECT id FROM items WHERE dedup_hash=?", (dedup_hash,))
    row = cur.fetchone()
    if row:
        conn.execute("UPDATE items SET last_seen_at_utc=? WHERE id=?", (now, int(row["id"])) )
        conn.commit()
        return int(row["id"]), False

    conn.execute(
        """
        INSERT INTO items(
          feed_id,guid,link,title,author,published_at,updated_at,doi,journal,
          abstract,abstract_source,content_snippet,raw_entry_json,dedup_hash,
          first_seen_at_utc,last_seen_at_utc
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            feed_id,
            entry.get("guid") or entry.get("id"),
            entry.get("link"),
            entry.get("title"),
            entry.get("author"),
            entry.get("published"),
            entry.get("updated"),
            entry.get("doi"),
            entry.get("journal") or entry.get("feedTitle"),
            entry.get("abstract"),
            entry.get("abstractSource"),
            entry.get("snippet") or entry.get("content_snippet"),
            json.dumps(entry, ensure_ascii=False),
            dedup_hash,
            now,
            now,
        ),
    )
    conn.commit()
    item_id = int(conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"])
    return item_id, True


def ensure_delivery(conn: sqlite3.Connection, *, item_id: int, channel: str, target: str | None, batch_id: str | None) -> int:
    now = utc_now_iso()
    # insert if not exists
    conn.execute(
        """
        INSERT INTO deliveries(item_id, channel, target, batch_id, status, created_at_utc)
        VALUES (?, ?, ?, ?, 'pending', ?)
        ON CONFLICT(item_id, channel, target) DO NOTHING
        """,
        (item_id, channel, target, batch_id, now),
    )
    conn.commit()
    row = conn.execute(
        "SELECT id FROM deliveries WHERE item_id=? AND channel=? AND (target IS ? OR target=?)",
        (item_id, channel, target, target),
    ).fetchone()
    return int(row["id"]) if row else -1


def mark_delivery(conn: sqlite3.Connection, delivery_id: int, *, status: str, error: str | None = None) -> None:
    conn.execute(
        "UPDATE deliveries SET status=?, sent_at_utc=?, error=? WHERE id=?",
        (status, utc_now_iso() if status == "sent" else None, error, delivery_id),
    )
    conn.commit()


def list_pending_items(conn: sqlite3.Connection, *, channel: str, target: str | None, limit: int = 200) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT i.*, f.url AS feed_url, f.title AS feed_title, d.id AS delivery_id, d.status AS delivery_status
        FROM deliveries d
        JOIN items i ON i.id = d.item_id
        JOIN feeds f ON f.id = i.feed_id
        WHERE d.channel = ?
          AND d.status IN ('pending','failed')
          AND (d.target IS ? OR d.target = ?)
        ORDER BY i.first_seen_at_utc ASC
        LIMIT ?
        """,
        (channel, target, target, int(limit)),
    ).fetchall()
