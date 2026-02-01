#!/usr/bin/env python3
"""Format Whisper verbose_json transcript into paragraph-based zh-TW markdown.

Input: --input transcript_verbose.json
Output: --out transcript.md

Heuristics:
- Merge small segments into paragraphs until:
  - duration >= max_seconds_per_para OR
  - character count >= max_chars_per_para AND the paragraph ends with sentence punctuation
- Add timestamp (mm:ss) per paragraph.

This is meant for readable transcripts, not subtitles.
"""

from __future__ import annotations

import argparse
import json
import math
import re


def mmss(sec: float) -> str:
    sec = max(0.0, float(sec))
    m = int(sec // 60)
    s = int(sec % 60)
    return f"{m:02d}:{s:02d}"


def clean_text(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    return s


def is_sentence_end(s: str) -> bool:
    return bool(re.search(r"[。！？!?]$", s))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-seconds", type=float, default=45.0)
    ap.add_argument("--max-chars", type=int, default=200)
    args = ap.parse_args()

    data = json.load(open(args.input, "r", encoding="utf-8"))
    segs = data.get("segments") or []

    paras = []
    cur = {"start": None, "end": None, "text": ""}

    def flush():
        if cur["start"] is None:
            return
        t = clean_text(cur["text"])
        if not t:
            return
        paras.append({"start": cur["start"], "end": cur["end"], "text": t})

    for sg in segs:
        t = clean_text(sg.get("text") or "")
        if not t:
            continue
        st = float(sg.get("start") or 0.0)
        ed = float(sg.get("end") or st)

        if cur["start"] is None:
            cur = {"start": st, "end": ed, "text": t}
            continue

        # append
        cur["text"] += (" " if cur["text"] else "") + t
        cur["end"] = ed

        duration = (cur["end"] - cur["start"]) if (cur["end"] is not None and cur["start"] is not None) else 0
        length = len(cur["text"])

        if duration >= args.max_seconds:
            flush()
            cur = {"start": None, "end": None, "text": ""}
            continue
        if length >= args.max_chars and is_sentence_end(cur["text"].rstrip()):
            flush()
            cur = {"start": None, "end": None, "text": ""}
            continue

    flush()

    out = []
    out.append(f"# 逐字稿（分段）\n")
    out.append(f"- Language: {data.get('language')}\n- Duration: {data.get('duration'):.1f}s\n")
    out.append("---\n")

    for p in paras:
        out.append(f"**[{mmss(p['start'])}–{mmss(p['end'])}]** {p['text']}\n")

    open(args.out, "w", encoding="utf-8").write("\n".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
