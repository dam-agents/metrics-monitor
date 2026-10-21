#!/usr/bin/env python3
"""Pull every metric in work/metrics.json from its source into work/data/snapshot.json.

Incremental: with a previous snapshot, only the last `refetch_hours` (late data, counters that
settle) and anything newer are pulled again; older buckets are kept as they are. Without one, the
whole `history_days` is pulled. The snapshot ends at the last complete bucket.

  scripts/fetch.py [--full] [--out PATH]
  scripts/fetch.py --check-metrics       validate work/metrics.json only, print ok
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.mm import SNAPSHOT, Sources, cfg_all, last_bucket_end, load_metrics, query_hash, source_label, source_names, utc  # noqa: E402


def series_key(metric, labels, n):
    by = metric["by"]
    if by:
        return labels.get(by) or "(none)"
    if n > 1:
        raise SystemExit(f"metric {metric['id']}: the query returns {n} series but `by` is not set; "
                         "aggregate them in the query, or set `by` to the label that tells them apart")
    return "all"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true", help="ignore the previous snapshot")
    ap.add_argument("--out", default=SNAPSHOT)
    ap.add_argument("--check-metrics", action="store_true", help="validate work/metrics.json and stop")
    a = ap.parse_args()

    conf = cfg_all()
    try:
        spec = load_metrics(conf=conf)
    except (ValueError, OSError) as e:
        raise SystemExit(f"work/metrics.json: {e}")
    if a.check_metrics:
        print(f"ok: {len(spec['metrics'])} metrics, {len(spec['derived'])} derived")
        return
    srcs = Sources(conf)
    step = spec["step"]
    end = last_bucket_end(step)
    prev = None
    if not a.full and os.path.exists(a.out):
        with open(a.out) as f:
            prev = json.load(f)
        if prev["meta"].get("step") != step or prev["meta"].get("source") != conf.get("source"):
            print("step or source changed since the last snapshot: full pull")
            prev = None
    if prev:
        first = prev["meta"]["start"]
        from_t = max(first, min(prev["meta"]["end"], end) - spec["refetch_hours"] * 3600)
    else:
        first = last_bucket_end(86400, end - spec["history_days"] * 86400)
        from_t = first

    out_series = {}
    qhash = {}
    t0 = time.time()
    for m in spec["metrics"]:
        qhash[m["id"]] = query_hash(m)
        m_from = from_t
        if prev and (prev["meta"].get("queries") or {}).get(m["id"]) != qhash[m["id"]]:
            print(f"{m['id']}: new metric or changed query: full history")
            m_from = first
        old = {} if m_from == first else {
            s["key"]: dict((int(t), v) for t, v in s["points"]) for s in prev["series"].get(m["id"], [])}
        ids = {k: v for k, v in old.items()}
        for pts in ids.values():
            for t in [t for t in pts if t >= m_from]:
                del pts[t]
        rows = srcs.of(m).range(m["query"], m_from, end, step) if m_from < end else []
        for s in rows:
            key = series_key(m, s["labels"], len(rows))
            pts = ids.setdefault(key, {})
            for t, v in s["points"]:
                if v is not None and first <= t < end:
                    pts[int(t)] = float(v)
        out_series[m["id"]] = [{"key": k, "points": sorted([t, v] for t, v in pts.items())}
                               for k, pts in sorted(ids.items()) if pts]
        n = sum(len(s["points"]) for s in out_series[m["id"]])
        print(f"{m['id']}: {len(out_series[m['id']])} series, {n} points")

    snap = {
        "meta": {
            "title": conf.get("title") or "Metrics",
            "source": conf.get("source"),
            "source_label": source_label(conf),
            "sources": {n: source_label(conf, n) for n in source_names(conf)},
            "step": step,
            "start": first,
            "end": end,
            "fetched_at": int(time.time()),
            "notes": spec.get("notes", []),
            "subtitle": conf.get("subtitle") or "",
            "derived": spec.get("derived", []),
            "queries": qhash,
        },
        "metrics": [{k: m.get(k) for k in ("id", "label", "unit", "kind", "combine", "by", "description", "kpi",
                                             "decimals", "group", "source") if m.get(k) is not None} for m in spec["metrics"]],
        "series": out_series,
    }
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    tmp = a.out + ".tmp"
    with open(tmp, "w") as f:
        json.dump(snap, f, separators=(",", ":"))
    os.replace(tmp, a.out)
    print(f"snapshot {utc(first)} .. {utc(end)}, pulled from {utc(from_t)} in {time.time() - t0:.0f}s -> {a.out}")


if __name__ == "__main__":
    main()
