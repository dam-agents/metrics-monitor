"""Synthetic data, deterministic, no network: for trying the kit before a real source is connected,
and for the offline tests. It plays an online shop. `query` names a generator: `orders`,
`response_time`, `servers`, `errors`. Values depend only on the bucket time, so a range query and
a window query agree exactly.
"""

import math

SERIES = {"orders": ["us-east", "us-west", "eu-west", "eu-central", "ap-south", "ap-east", "sa-east"],
          "response_time": ["all"], "servers": ["web", "worker"], "errors": ["all"]}
LABEL = {"orders": "region", "servers": "pool"}
SERVERS = {"web": 6.0, "worker": 3.0}


def value(gen, key, t):
    h = (t // 3600) % 24
    daily = 0.6 + 0.4 * math.sin((h - 9) / 24 * 2 * math.pi)
    i = (SERIES[gen].index(key) + 1) if key in SERIES[gen] else 1
    if gen == "orders":
        return round(120 * daily / i + (t // 3600) % 7, 3)
    if gen == "response_time":
        return round(0.15 + 0.15 * daily, 4)
    if gen == "servers":
        return SERVERS[key]
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
                if query.strip() == "response_time":
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
            v = sum(vals) / len(vals) if g == "response_time" else sum(vals)
            out.append({"labels": self._labels(g, key), "value": v})
        return out

    def raw(self, query, at):
        return self.window(query, at - 3600, at)
