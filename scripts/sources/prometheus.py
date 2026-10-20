"""Prometheus-compatible HTTP API: Prometheus, Mimir, Thanos, Cortex, VictoriaMetrics.

CONFIG.md keys:
  source_url       base URL up to and including the API prefix's parent, e.g.
                   https://mimir.example.com/prometheus  or  http://prometheus:9090
  source_headers   optional, 'X-Scope-OrgID: tenant; Other: value' (credentials come from a
                   platform connection the gateway injects, never from here)
  source_insecure  optional, 1 to skip TLS verification (self-signed routes)
  max_query_hours  optional, longest range per request (Mimir's max query length), default 720

Queries are PromQL. `$step` is replaced by the bucket length ("3600s") in range queries and by the
whole window in window queries, so one expression serves both:
  sum by (team) (increase(requests_total[$step]))
Prometheus stamps a range point at the END of its lookback; this adapter shifts it to the bucket start.
"""

import urllib.parse

from sources.http import get_json, parse_headers


class Source:
    name = "prometheus"

    def __init__(self, conf):
        self.base = (conf.get("source_url") or "").rstrip("/")
        if not self.base:
            raise SystemExit("work/CONFIG.md: source_url is required for source prometheus")
        self.headers = parse_headers(conf.get("source_headers"))
        self.headers["Content-Type"] = "application/x-www-form-urlencoded"
        self.insecure = str(conf.get("source_insecure", "")).lower() in ("1", "true", "yes")
        self.max_hours = int(conf.get("max_query_hours") or 720)

    def _api(self, path, params):
        out = get_json(f"{self.base}/api/v1/{path}", data=urllib.parse.urlencode(params),
                       headers=self.headers, insecure=self.insecure)
        if out.get("status") != "success":
            raise RuntimeError(f"{out.get('errorType')}: {out.get('error')}")
        return out["data"]

    @staticmethod
    def _labels(metric):
        return {k: v for k, v in metric.items() if k != "__name__"}

    def range(self, query, start, end, step):
        q = query.replace("$step", f"{step}s")
        merged = {}
        chunk = max(step, (self.max_hours * 3600 // step) * step)
        t = start
        while t < end:
            t2 = min(end, t + chunk)
            # points at t+step .. t2 cover buckets [t, t2)
            data = self._api("query_range", {"query": q, "start": t + step, "end": t2, "step": step})
            for s in data.get("result", []):
                labels = self._labels(s["metric"])
                key = tuple(sorted(labels.items()))
                pts = merged.setdefault(key, {"labels": labels, "points": {}})["points"]
                for ts, v in s["values"]:
                    pts[int(float(ts)) - step] = float(v)
            t = t2
        return [{"labels": s["labels"], "points": sorted(s["points"].items())} for s in merged.values()]

    def window(self, query, start, end):
        q = query.replace("$step", f"{int(end - start)}s")
        data = self._api("query", {"query": q, "time": end})
        if data.get("resultType") == "scalar":
            return [{"labels": {}, "value": float(data["result"][1])}]
        return [{"labels": self._labels(s["metric"]), "value": float(s["value"][1])} for s in data.get("result", [])]

    def raw(self, query, at):
        return self._api("query", {"query": query, "time": at})
