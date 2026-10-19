#!/usr/bin/env python3
"""Cross-check the dashboard's numbers against independent queries.

For every metric: the value the dashboard shows for the window (computed from the snapshot's
buckets, the same rule the page uses) against one `window` query over the same window, straight
from the source. A metric may give `verify_query` to check against a different, independent
measurement of the same thing (another table, another exporter); it is compared in total.

  scripts/verify.py [--hours 168] [--check]

Prints one line per metric; with --check, exits 2 if any differs by more than its
`tolerance_pct` (default 1%). `avg`/`last` metrics of a window query are only comparable when the
query itself averages, so they compare when `verify_query` is set and are otherwise listed as
"not cross-checked".
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.mm import SNAPSHOT, cfg_all, combine, fmt_num, load_metrics, range_value, source, utc  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=int, default=168)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--snapshot", default=SNAPSHOT)
    a = ap.parse_args()
    spec = load_metrics()
    snap = json.load(open(a.snapshot))
    src = source(cfg_all())
    end = snap["meta"]["end"]
    start = max(snap["meta"]["start"], end - a.hours * 3600)
    print(f"window {utc(start)} .. {utc(end)} ({(end - start) // 3600} h)")
    bad = 0
    for m in spec["metrics"]:
        series = snap["series"].get(m["id"], [])
        dash = range_value(m, series, start, end)
        q = m.get("verify_query")
        if not q and m["kind"] != "sum":
            print(f"skip  {m['id']}: {m['kind']} metric with no verify_query: not cross-checked")
            continue
        rows = src.window(q or m["query"], start, end)
        vals = [r["value"] for r in rows if r["value"] is not None]
        ind = combine(vals, "sum" if m["kind"] == "sum" else m["combine"]) if vals else None
        if dash is None and ind is None:
            print(f"ok    {m['id']}: no data in either")
            continue
        if dash is None or ind is None:
            bad += 1
            print(f"FAIL  {m['id']}: dashboard {fmt_num(dash, m['unit'])} vs independent {fmt_num(ind, m['unit'])}")
            continue
        diff = 0.0 if dash == ind else abs(dash - ind) / max(abs(ind), abs(dash)) * 100
        tol = m["tolerance_pct"]
        tag = "ok  " if diff <= tol else "FAIL"
        bad += diff > tol
        print(f"{tag}  {m['id']}: dashboard {fmt_num(dash, m['unit'])} vs independent {fmt_num(ind, m['unit'])} "
              f"({diff:.2f}%, tolerance {tol}%){' via verify_query' if q else ''}")
    if a.check and bad:
        sys.exit(2)


if __name__ == "__main__":
    main()
