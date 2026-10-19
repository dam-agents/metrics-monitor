"""ClickHouse over its HTTP interface (port 8123, or 8443 with TLS).

CONFIG.md keys:
  source_url       e.g. https://clickhouse.example.com:8443
  source_database  optional default database
  source_headers   optional extra headers; credentials come from a platform connection that the
                   gateway injects (X-ClickHouse-User / X-ClickHouse-Key, or Authorization)
  source_insecure  optional, 1 to skip TLS verification
  max_query_hours  optional, longest range per request, default 2160

Queries are SQL returning one row per bucket and series, with a column `t` (bucket start) and a
column `value`; every other column is a label. Placeholders, filled in by this adapter:
  $bucket(col)  the bucket start of DateTime column `col`, as unix seconds
  $range(col)   col >= start AND col < end
  $start $end $step   numbers (unix seconds, seconds)
Example:
  SELECT $bucket(ts) AS t, model, sum(tokens) AS value
  FROM requests WHERE $range(ts) GROUP BY t, model
A window query is the same SQL with one bucket spanning the whole window.
Values are passed as numbers the adapter computes itself, never user text, so there is nothing to escape.
"""

import json
import re
import urllib.parse

from sources.http import parse_headers, request


class Source:
    name = "clickhouse"

    def __init__(self, conf):
        self.base = (conf.get("source_url") or "").rstrip("/")
        if not self.base:
            raise SystemExit("work/CONFIG.md: source_url is required for source clickhouse")
        self.db = conf.get("source_database")
        self.headers = parse_headers(conf.get("source_headers"))
        self.insecure = str(conf.get("source_insecure", "")).lower() in ("1", "true", "yes")
        self.max_hours = int(conf.get("max_query_hours") or 2160)

    @staticmethod
    def fill(sql, start, end, step):
        start, end, step = int(start), int(end), int(step)
        sql = re.sub(r"\$bucket\(\s*([^)]+?)\s*\)",
                     lambda m: f"({start} + intDiv(toUInt32(toUnixTimestamp({m.group(1)})) - {start}, {step}) * {step})", sql)
        sql = re.sub(r"\$range\(\s*([^)]+?)\s*\)",
                     lambda m: f"({m.group(1)} >= toDateTime({start}) AND {m.group(1)} < toDateTime({end}))", sql)
        return sql.replace("$start", str(start)).replace("$end", str(end)).replace("$step", str(step))

    def _rows(self, sql):
        params = {"default_format": "JSONEachRow"}
        if self.db:
            params["database"] = self.db
        out = request(f"{self.base}/?{urllib.parse.urlencode(params)}", data=sql.rstrip().rstrip(";"),
                      headers=self.headers, insecure=self.insecure)
        return [json.loads(line) for line in out.splitlines() if line.strip()]

    @staticmethod
    def _split(row):
        labels = {k: str(v) for k, v in row.items() if k not in ("t", "value")}
        return labels, (None if row.get("value") is None else float(row["value"]))

    def range(self, query, start, end, step):
        merged = {}
        chunk = max(step, (self.max_hours * 3600 // step) * step)
        t = start
        while t < end:
            t2 = min(end, t + chunk)
            for row in self._rows(self.fill(query, t, t2, step)):
                labels, v = self._split(row)
                key = tuple(sorted(labels.items()))
                merged.setdefault(key, {"labels": labels, "points": {}})["points"][int(row["t"])] = v
            t = t2
        return [{"labels": s["labels"], "points": sorted(s["points"].items())} for s in merged.values()]

    def window(self, query, start, end):
        out = []
        for row in self._rows(self.fill(query, start, end, end - start)):
            labels, v = self._split(row)
            out.append({"labels": labels, "value": v})
        return out

    def raw(self, query, at):
        return self._rows(query)
