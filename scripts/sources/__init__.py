"""Source adapters. Each module defines `class Source(conf)` with two methods:

    range(query, start, end, step) -> [{"labels": {...}, "points": [[t, value], ...]}, ...]
        one point per bucket [t, t + step), t = bucket start in unix seconds, start..end step-aligned
    window(query, start, end) -> [{"labels": {...}, "value": float}, ...]
        one value per series for the whole window [start, end), computed by the source in one query

`window` is what verify.py and ask.py use: an independent single query, not a sum of the buckets
the dashboard holds. Adding a source is one file here; see docs/sources.md.
"""
