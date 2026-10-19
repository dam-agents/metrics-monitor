#!/usr/bin/env python3
"""Is a new snapshot fresh and complete, compared with the previous one? Prints ok/WARN/FAIL lines.

  scripts/check_snapshot.py NEW [PREVIOUS]

FAIL (exit 4), so the refresh keeps the previous snapshot:
  - the data ends more than `max_lag_hours` before now
  - the history start moved later (history lost)
  - a metric, or a series that had data in the last 7 days of the previous snapshot, disappeared
  - a `sum` metric's total up to the previous end dropped by more than 0.5% (data lost upstream)
  - no metric has any data in the last `expect_activity_hours`
WARN only: a metric with no data in its last bucket, a new series, buckets missing in the middle.
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.mm import load_metrics, utc  # noqa: E402

FAILS = 0


def ok(msg):
    print(f"ok    {msg}")


def warn(msg):
    print(f"WARN  {msg}")


def fail(msg):
    global FAILS
    FAILS += 1
    print(f"FAIL  {msg}")


def total(series, until):
    return sum(v for s in series for t, v in s["points"] if t < until)


def main():
    new_p = sys.argv[1]
    prev_p = sys.argv[2] if len(sys.argv) > 2 else None
    spec = load_metrics()
    new = json.load(open(new_p))
    prev = json.load(open(prev_p)) if prev_p and os.path.exists(prev_p) else None
    meta, step = new["meta"], new["meta"]["step"]

    lag = (time.time() - meta["end"]) / 3600
    if lag > spec["max_lag_hours"] + step / 3600:
        fail(f"data ends {utc(meta['end'])}, {lag:.1f} h ago (allowed {spec['max_lag_hours']} h)")
    else:
        ok(f"data ends {utc(meta['end'])} ({lag:.1f} h ago)")

    recent = meta["end"] - spec["expect_activity_hours"] * 3600
    active = [m for m, ss in new["series"].items() if any(t >= recent for s in ss for t, _ in s["points"])]
    if active:
        ok(f"data in the last {spec['expect_activity_hours']} h: {len(active)}/{len(new['series'])} metrics")
    else:
        fail(f"no metric has data in the last {spec['expect_activity_hours']} h")

    for m in spec["metrics"]:
        ss = new["series"].get(m["id"], [])
        if not ss:
            (fail if prev and prev["series"].get(m["id"]) else warn)(f"{m['id']}: no data at all")
            continue
        last = meta["end"] - step
        if not any(t == last for s in ss for t, _ in s["points"]):
            warn(f"{m['id']}: no value in the last bucket ({utc(last)})")
        times = sorted({t for s in ss for t, _ in s["points"]})
        holes = sum(1 for a, b in zip(times, times[1:]) if b - a > step)
        if holes:
            warn(f"{m['id']}: {holes} gap(s) in the middle of the history")

    if not prev:
        ok("no previous snapshot to compare with")
    else:
        pm = prev["meta"]
        if meta["start"] > pm["start"]:
            fail(f"history now starts {utc(meta['start'])}, was {utc(pm['start'])}")
        else:
            ok(f"history start {utc(meta['start'])}")
        for m in spec["metrics"]:
            if (pm.get("queries") or {}).get(m["id"]) != (meta.get("queries") or {}).get(m["id"]):
                warn(f"{m['id']}: new metric or changed query: not compared with the previous snapshot")
                continue
            old, cur = prev["series"].get(m["id"], []), new["series"].get(m["id"], [])
            week = pm["end"] - 7 * 86400
            old_keys = {s["key"] for s in old if any(t >= week for t, _ in s["points"])}
            cur_keys = {s["key"] for s in cur}
            if old_keys - cur_keys:
                fail(f"{m['id']}: series gone: {', '.join(sorted(old_keys - cur_keys))}")
            if cur_keys - {s['key'] for s in old}:
                warn(f"{m['id']}: new series: {', '.join(sorted(cur_keys - {s['key'] for s in old}))}")
            if m["kind"] == "sum" and old:
                a, b = total(old, pm["end"]), total(cur, pm["end"])
                if a > 0 and b < a * 0.995:
                    fail(f"{m['id']}: total up to {utc(pm['end'])} fell {100 * (1 - b / a):.2f}% ({a:.6g} -> {b:.6g})")
                else:
                    ok(f"{m['id']}: total up to the previous end kept ({(b / a - 1) * 100 if a else 0:+.2f}%)")
    sys.exit(4 if FAILS else 0)


if __name__ == "__main__":
    main()
