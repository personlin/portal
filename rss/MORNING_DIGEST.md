# Morning Digest (早安彙整) — Ops Notes

This is the reliable (outbox-based) morning digest pipeline.

## Files (outbox)

All outputs are persisted under:

- `/home/person/.openclaw/workspace/rss/outbox/`

Per day (Asia/Taipei date):

- `morning-YYYY-MM-DD.json` — full payload + sendStatus
- `morning-YYYY-MM-DD.email.txt` — plain text fallback
- `morning-YYYY-MM-DD.email.html` — rich HTML

Email send log:

- `email_send_log.jsonl` — append-only JSONL of send attempts (metadata only)

## Build

Generate today’s digest + write outbox:

```bash
python3 /home/person/.openclaw/workspace/rss/morning_digest_build.py > /tmp/morning_digest.json
```

## Send (Email)

Send from today’s outbox (skips if already marked sent):

```bash
python3 /home/person/.openclaw/workspace/rss/morning_digest_send.py --send-email
```

Resend even if already marked sent (force):

```bash
python3 /home/person/.openclaw/workspace/rss/morning_digest_send.py --send-email --force-email
```

Send a specific date:

```bash
python3 /home/person/.openclaw/workspace/rss/morning_digest_send.py --date 2026-02-06 --send-email --force-email
```

## Send (Telegram)

Telegram delivery uses OpenClaw’s message tool (cannot be done purely inside Python).

1) Get the Telegram text:

```bash
python3 /home/person/.openclaw/workspace/rss/morning_digest_send.py --get-telegram
```

2) Send the text via OpenClaw (functions.message) to chat id `401392371`.

3) Mark success back to outbox:

```bash
python3 /home/person/.openclaw/workspace/rss/morning_digest_send.py --mark-telegram-sent --telegram-ok
```

If sending fails, mark error:

```bash
python3 /home/person/.openclaw/workspace/rss/morning_digest_send.py \
  --mark-telegram-sent \
  --telegram-error "<error>"
```

## Cron jobs

- Morning digest main run: 08:00 Asia/Taipei
- Catch-up (補寄): 08:20 Asia/Taipei

Both runs:
- build → outbox
- send email (retries + log)
- send telegram (if needed) + write back sendStatus
