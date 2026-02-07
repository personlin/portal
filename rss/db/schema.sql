-- GeoSci RSS reliability DB schema
-- SQLite

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- 1) Feeds master
CREATE TABLE IF NOT EXISTS feeds (
  id INTEGER PRIMARY KEY,
  url TEXT NOT NULL UNIQUE,
  title TEXT,
  publisher TEXT,
  category TEXT,
  enabled INTEGER NOT NULL DEFAULT 1,
  priority INTEGER NOT NULL DEFAULT 0,

  etag TEXT,
  last_modified TEXT,

  last_fetch_at_utc TEXT,
  last_success_at_utc TEXT,
  last_error TEXT,
  consecutive_failures INTEGER NOT NULL DEFAULT 0,
  next_fetch_after_utc TEXT,

  created_at_utc TEXT NOT NULL,
  updated_at_utc TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_feeds_enabled_nextfetch ON feeds(enabled, next_fetch_after_utc, priority);

-- 2) Fetch runs
CREATE TABLE IF NOT EXISTS fetch_runs (
  id INTEGER PRIMARY KEY,
  kind TEXT NOT NULL DEFAULT 'geosci',
  started_at_utc TEXT NOT NULL,
  finished_at_utc TEXT,
  ok INTEGER,
  feed_count INTEGER,
  success_count INTEGER,
  error_count INTEGER,
  notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_fetch_runs_kind_started ON fetch_runs(kind, started_at_utc);

-- 3) Per-feed fetch logs per run
CREATE TABLE IF NOT EXISTS feed_fetch_logs (
  id INTEGER PRIMARY KEY,
  run_id INTEGER NOT NULL,
  feed_id INTEGER NOT NULL,
  started_at_utc TEXT NOT NULL,
  finished_at_utc TEXT,
  ok INTEGER,
  http_status INTEGER,
  bytes INTEGER,
  new_items_count INTEGER,
  error TEXT,
  FOREIGN KEY(run_id) REFERENCES fetch_runs(id) ON DELETE CASCADE,
  FOREIGN KEY(feed_id) REFERENCES feeds(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_feed_fetch_logs_run ON feed_fetch_logs(run_id);
CREATE INDEX IF NOT EXISTS idx_feed_fetch_logs_feed ON feed_fetch_logs(feed_id, started_at_utc);

-- 4) Items
CREATE TABLE IF NOT EXISTS items (
  id INTEGER PRIMARY KEY,
  feed_id INTEGER NOT NULL,

  guid TEXT,
  link TEXT,
  title TEXT,
  title_zh_tw TEXT,
  author TEXT,
  published_at TEXT,
  updated_at TEXT,

  doi TEXT,
  journal TEXT,

  abstract TEXT,
  abstract_zh_tw TEXT,
  abstract_source TEXT,
  content_snippet TEXT,

  summary_en TEXT,
  summary_zh_tw TEXT,

  enrich_status TEXT,          -- pending|ok|failed
  enrich_error TEXT,
  enriched_at_utc TEXT,

  raw_entry_json TEXT,
  dedup_hash TEXT NOT NULL UNIQUE,

  first_seen_at_utc TEXT NOT NULL,
  last_seen_at_utc TEXT NOT NULL,

  FOREIGN KEY(feed_id) REFERENCES feeds(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_items_feed_seen ON items(feed_id, first_seen_at_utc);
CREATE INDEX IF NOT EXISTS idx_items_published ON items(published_at);
CREATE INDEX IF NOT EXISTS idx_items_doi ON items(doi);

-- 5) Deliveries (per channel/target)
CREATE TABLE IF NOT EXISTS deliveries (
  id INTEGER PRIMARY KEY,
  item_id INTEGER NOT NULL,
  channel TEXT NOT NULL,
  target TEXT,
  batch_id TEXT,
  status TEXT NOT NULL DEFAULT 'pending', -- pending|sent|failed
  created_at_utc TEXT NOT NULL,
  sent_at_utc TEXT,
  error TEXT,
  UNIQUE(item_id, channel, target),
  FOREIGN KEY(item_id) REFERENCES items(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_deliveries_status ON deliveries(status, created_at_utc);
CREATE INDEX IF NOT EXISTS idx_deliveries_batch ON deliveries(batch_id);

-- 6) Digest batches (e.g., GeoSci gist history)
CREATE TABLE IF NOT EXISTS digest_batches (
  id INTEGER PRIMARY KEY,
  kind TEXT NOT NULL,               -- e.g., 'geosci'
  date_taipei TEXT NOT NULL,        -- YYYY-MM-DD
  batch_id TEXT NOT NULL UNIQUE,    -- correlates with marking deliveries
  gist_url TEXT,
  gist_id TEXT,
  included_count INTEGER NOT NULL DEFAULT 0,
  remaining_pending_after INTEGER,
  status TEXT NOT NULL DEFAULT 'created',  -- created|failed
  error TEXT,
  created_at_utc TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_digest_batches_kind_date ON digest_batches(kind, date_taipei);

-- 7) Digest deliveries (morning digest send status)
CREATE TABLE IF NOT EXISTS digest_deliveries (
  id INTEGER PRIMARY KEY,
  kind TEXT NOT NULL,            -- e.g., 'morning_digest'
  date_taipei TEXT NOT NULL,     -- YYYY-MM-DD
  channel TEXT NOT NULL,         -- 'telegram'|'email'
  target TEXT NOT NULL,          -- telegram chat id / email address
  batch_id TEXT,
  status TEXT NOT NULL DEFAULT 'pending', -- pending|sent|failed
  created_at_utc TEXT NOT NULL,
  sent_at_utc TEXT,
  error TEXT,
  UNIQUE(kind, date_taipei, channel, target)
);

CREATE INDEX IF NOT EXISTS idx_digest_deliveries_status ON digest_deliveries(kind, status, created_at_utc);
