"""Synthetic data, deterministic, no network: for trying the kit before a real source is connected,
and for the offline tests. It plays a software product. `query` names a generator: `sessions`,
`page_load`, `signups`, `errors`. Values depend only on the bucket time, so a range query and
a window query agree exactly.
"""

import math

SERIES = {"sessions": ["dashboard", "search", "editor", "reports", "settings", "integrations", "api"],
          "page_load": ["all"], "signups": ["free", "pro"], "errors": ["all"]}
LABEL = {"sessions": "feature", "signups": "plan"}
SIGNUPS = {"free": 6.0, "pro": 3.0}


def value(gen, key, t):
    h = (t // 3600) % 24
    daily = 0.6 + 0.4 * math.sin((h - 9) / 24 * 2 * math.pi)
    i = (SERIES[gen].index(key) + 1) if key in SERIES[gen] else 1
    if gen == "sessions":
        return round(120 * daily / i + (t // 3600) % 7, 3)
    if gen == "page_load":
        return round(0.8 + 0.6 * daily, 4)
    if gen == "signups":
        return round(SIGNUPS[key] * daily, 3)
    return float((t // 3600) % 5 == 0)


class Source:
    name = "demo"

    def __init__(self, conf):
        pass

    def _labels(self, gen, key):
        return {} if key == "all" else {LABEL[gen]: key}

    def range(self, query, start, end, step):
        out = []
        for key in SERIES[query.strip()]:
            pts = []
            for t in range(int(start), int(end), int(step)):
                # sum of the hours inside the bucket, so any step stays consistent with window()
                hours = range(t, t + int(step), 3600)
                if query.strip() == "page_load":
                    v = sum(value(query.strip(), key, x) for x in hours) / len(hours)
                else:
                    v = sum(value(query.strip(), key, x) for x in hours)
                pts.append([t, v])
            out.append({"labels": self._labels(query.strip(), key), "points": pts})
        return out

    def window(self, query, start, end):
        g = query.strip()
        hours = range(int(start), int(end), 3600)
        out = []
        for key in SERIES[g]:
            vals = [value(g, key, x) for x in hours]
            v = sum(vals) / len(vals) if g == "page_load" else sum(vals)
            out.append({"labels": self._labels(g, key), "value": v})
        return out

    def raw(self, query, at):
        return self.window(query, at - 3600, at)
