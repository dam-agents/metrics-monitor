#!/usr/bin/env python3
"""Live answers from the sources, for questions in Slack or chat. Never reads the snapshot.

  scripts/ask.py list                                    the metrics and what they mean
  scripts/ask.py <metric-id> [--since 24h] [--until now] [--by-series]
  scripts/ask.py raw '<query>' [--since 24h] [--source NAME]   any query in that source's language

Prints the value with its unit, the exact UTC window and how it was measured, which is what every
answer must state (CLAUDE.md -> **Answering questions**).
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.mm import Sources, cfg_all, combine, fmt_num, load_metrics, parse_dur, source_label, utc  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("what")
    ap.add_argument("query", nargs="?")
    ap.add_argument("--since", default="24h")
    ap.add_argument("--until", default="now")
    ap.add_argument("--by-series", action="store_true")
    ap.add_argument("--source", help="for raw: a source name from work/CONFIG.md (default: `source`)")
    a = ap.parse_args()
    conf = cfg_all()
    spec = load_metrics(conf=conf)
    if a.what == "list":
        for m in spec["metrics"]:
            print(f"{m['id']:<24} {m['label']} ({m['unit']}, {m['kind']}{', by ' + m['by'] if m['by'] else ''}{', from ' + m['source'] if m['source'] else ''})"
                  f"{' - ' + m['description'] if m.get('description') else ''}")
        return
    srcs = Sources(conf)
    now = int(time.time())
    end = now if a.until == "now" else now - parse_dur(a.until)
    start = end - parse_dur(a.since)
    win = f"{utc(start)} .. {utc(end)}"
    if a.what == "raw":
        if not a.query:
            raise SystemExit("raw needs a query")
        print(f"window {win}")
        print(f"source: {source_label(conf, a.source)}")
        print(json.dumps(srcs.get(a.source).window(a.query, start, end), indent=1))
        return
    m = next((m for m in spec["metrics"] if m["id"] == a.what), None)
    if not m:
        raise SystemExit(f"unknown metric {a.what}; `scripts/ask.py list` shows them")
    rows = srcs.of(m).window(m["query"], start, end)
    vals = [r["value"] for r in rows if r["value"] is not None]
    how = "sum" if m["kind"] == "sum" else m["combine"]
    print(f"{m['label']}: {fmt_num(combine(vals, how) if vals else None, m['unit'])}")
    print(f"window: {win} ({(end - start) / 3600:g} h), source: {source_label(conf, m['source'])}")
    print(f"measured: {m.get('description') or m['query']}")
    if m["kind"] != "sum":
        print(f"note: a single window query; series combined by {how}")
    if a.by_series or m["by"]:
        for r in sorted(rows, key=lambda r: -(r["value"] or 0)):
            key = r["labels"].get(m["by"]) if m["by"] else json.dumps(r["labels"])
            print(f"  {key or '(none)'}: {fmt_num(r['value'], m['unit'])}")


if __name__ == "__main__":
    main()
