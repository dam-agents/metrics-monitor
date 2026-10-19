"""Shared helpers for the metrics-monitor scripts: paths, work/CONFIG.md, work/metrics.json, the
source adapter, and time formatting. Standard library only.

Paths: the definition is this repository (normally $HOME); runtime state is $MM_WORK, by default
$HOME/work. Tests point MM_WORK at a temporary directory.
"""

import importlib
import json
import math
import os
import re
import sys
import time

DEF = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORK = os.environ.get("MM_WORK") or os.path.join(os.path.expanduser("~"), "work")
CONFIG = os.path.join(WORK, "CONFIG.md")
METRICS = os.path.join(WORK, "metrics.json")
SNAPSHOT = os.path.join(WORK, "data", "snapshot.json")

KINDS = ("sum", "avg", "last")
COMBINE = ("sum", "mean", "max")


def cfg(key, default=None):
    """First `- key: value` bullet of work/CONFIG.md (case-insensitive key, backticks stripped)."""
    try:
        with open(CONFIG) as f:
            for line in f:
                m = re.match(r"^[-*]?\s*([A-Za-z0-9_]+)\s*:\s*(.*)$", line)
                if m and m.group(1).lower() == key.lower():
                    v = m.group(2).replace("`", "").strip()
                    return v if v else default
    except FileNotFoundError:
        pass
    return default


def cfg_all():
    out = {}
    try:
        with open(CONFIG) as f:
            for line in f:
                m = re.match(r"^[-*]\s*([A-Za-z0-9_]+)\s*:\s*(.*)$", line)
                if m and m.group(1).lower() not in out:
                    out[m.group(1).lower()] = m.group(2).replace("`", "").strip()
    except FileNotFoundError:
        pass
    return out


def load_metrics(path=None):
    """work/metrics.json with defaults applied. Raises ValueError with every problem found."""
    path = path or METRICS
    with open(path) as f:
        spec = json.load(f)
    errs = []
    spec.setdefault("step", 3600)
    spec.setdefault("history_days", 90)
    spec.setdefault("max_lag_hours", 2)
    spec.setdefault("expect_activity_hours", 6)
    spec.setdefault("refetch_hours", 48)
    if not isinstance(spec["step"], int) or spec["step"] < 60:
        errs.append("step must be an integer number of seconds >= 60")
    ms = spec.get("metrics")
    if not isinstance(ms, list) or not ms:
        errs.append("metrics must be a non-empty list")
        ms = []
    seen = set()
    for i, m in enumerate(ms):
        where = f"metrics[{i}]"
        mid = m.get("id")
        if not isinstance(mid, str) or not re.match(r"^[a-z0-9][a-z0-9_-]*$", mid or ""):
            errs.append(f"{where}: id must be lowercase letters, digits, - or _")
        elif mid in seen:
            errs.append(f"{where}: duplicate id {mid}")
        seen.add(mid)
        for k in ("label", "unit", "query"):
            if not m.get(k):
                errs.append(f"{where} ({mid}): missing {k}")
        m.setdefault("kind", "sum")
        if m["kind"] not in KINDS:
            errs.append(f"{where} ({mid}): kind must be one of {KINDS}")
        m.setdefault("combine", "sum" if m["kind"] == "sum" else "mean")
        if m["combine"] not in COMBINE:
            errs.append(f"{where} ({mid}): combine must be one of {COMBINE}")
        m.setdefault("by", None)
        m.setdefault("tolerance_pct", 1.0)
        kpi = m.get("kpi")
        if kpi is not None:
            if kpi.get("op") not in (">=", "<="):
                errs.append(f"{where} ({mid}): kpi.op must be >= or <=")
            if not isinstance(kpi.get("target"), (int, float)):
                errs.append(f"{where} ({mid}): kpi.target must be a number")
            if kpi.get("per") not in (None, "range", "day"):
                errs.append(f"{where} ({mid}): kpi.per must be range or day")
            if not kpi.get("set_by"):
                errs.append(f"{where} ({mid}): kpi.set_by must say who set it and when")
    ids = {m.get("id") for m in ms}
    for i, d in enumerate(spec.setdefault("derived", [])):
        where = f"derived[{i}] ({d.get('id')})"
        if not d.get("id") or d["id"] in ids:
            errs.append(f"{where}: needs an id that no metric uses")
        ids.add(d.get("id"))
        if d.get("op") not in ("times", "ratio"):
            errs.append(f"{where}: op must be times or ratio")
        if d.get("a") not in {m.get("id") for m in ms}:
            errs.append(f"{where}: a must name a metric")
        if d.get("op") == "ratio" and d.get("b") not in {m.get("id") for m in ms}:
            errs.append(f"{where}: b must name a metric")
        if d.get("op") == "times" and not isinstance(d.get("factor"), (int, float)):
            errs.append(f"{where}: times needs a numeric factor")
        a_m = next((m for m in ms if m.get("id") == d.get("a")), None)
        if d.get("op") == "times" and a_m and a_m.get("kind") != "sum":
            errs.append(f"{where}: times multiplies a total, so `a` must be a sum metric (e.g. GPU-hours, not GPUs)")
        if d.get("op") == "times" and not d.get("set_by"):
            errs.append(f"{where}: a rate set by hand needs set_by (who, when)")
        if not d.get("label") or not d.get("unit"):
            errs.append(f"{where}: needs label and unit")
    if errs:
        raise ValueError("; ".join(errs))
    return spec


def source(conf=None):
    """The adapter named by `source` in CONFIG.md (scripts/sources/<name>.py, class Source)."""
    conf = conf if conf is not None else cfg_all()
    kind = conf.get("source")
    if not kind or not re.match(r"^[a-z0-9_]+$", kind):
        raise SystemExit("work/CONFIG.md has no valid `source` key (prometheus, clickhouse, command)")
    scripts = os.path.join(DEF, "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    try:
        mod = importlib.import_module(f"sources.{kind}")
    except ModuleNotFoundError:
        raise SystemExit(f"no adapter scripts/sources/{kind}.py for source `{kind}`")
    return mod.Source(conf)


def parse_dur(s):
    """'90m', '24h', '7d', '2w' or plain seconds -> seconds."""
    m = re.match(r"^(\d+(?:\.\d+)?)([smhdw]?)$", str(s).strip())
    if not m:
        raise ValueError(f"bad duration: {s}")
    return int(float(m.group(1)) * {"": 1, "s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}[m.group(2)])


def fmt_dur(sec):
    for unit, n in (("w", 604800), ("d", 86400), ("h", 3600), ("m", 60)):
        if sec % n == 0:
            return f"{sec // n}{unit}"
    return f"{sec}s"


def utc(ts):
    return time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(ts))


def last_bucket_end(step, now=None):
    now = time.time() if now is None else now
    return int(now // step) * step


def combine(values, how):
    values = [v for v in values if v is not None and not math.isnan(v)]
    if not values:
        return None
    if how == "sum":
        return sum(values)
    if how == "max":
        return max(values)
    return sum(values) / len(values)


def range_value(metric, series, start, end):
    """The dashboard's "all series" value of a metric over [start, end): per bucket the series are
    combined (`combine`), then buckets are summed (kind sum), averaged over buckets with data (avg),
    or the last bucket is taken (last). The template implements the same rule."""
    buckets = {}
    for s in series:
        for t, v in s["points"]:
            if start <= t < end:
                buckets.setdefault(t, []).append(v)
    per = {t: combine(vs, metric["combine"]) for t, vs in buckets.items()}
    per = {t: v for t, v in per.items() if v is not None}
    if not per:
        return None
    if metric["kind"] == "sum":
        return sum(per.values())
    if metric["kind"] == "last":
        return per[max(per)]
    return sum(per.values()) / len(per)


def fmt_num(v, unit=""):
    if v is None:
        return "no data"
    a = abs(v)
    for div, suf in ((1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")):
        if a >= div:
            s = f"{v / div:.3g}{suf}"
            break
    else:
        s = f"{v:.3g}" if a < 100 else f"{v:.0f}"
    return f"{s} {unit}".strip()
