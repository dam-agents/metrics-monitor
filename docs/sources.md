# Data sources

The kit doesn't depend on any one data source. `source` in `work/CONFIG.md` names an adapter,
`scripts/sources/<source>.py`, and every script (fetch, verify, ask) talks to the source only
through it. Read this when you connect a source, or meet one that no adapter covers.

## The adapters

| `source` | For | Query language |
| --- | --- | --- |
| `prometheus` | Prometheus, Grafana Mimir, Thanos, Cortex, VictoriaMetrics | PromQL |
| `clickhouse` | ClickHouse over HTTP (self-hosted or Cloud) | SQL |
| `command` | anything a script can read: Postgres (`psql`), BigQuery (`bq`), Snowflake, a REST API, a CSV export | a shell command |
| `demo` | trying the kit with synthetic data | generator names |

Each module's docstring lists its `work/CONFIG.md` keys and placeholders.

### prometheus

- `source_url`: the parent of `/api/v1`, e.g. `http://prometheus:9090` or
  `https://mimir.example.com/prometheus`.
- `source_headers`: e.g. `X-Scope-OrgID: tenant` for multi-tenant Mimir or Cortex.
- `source_insecure: 1`: skip TLS verification (self-signed routes).
- `max_query_hours`: the longest range per request. Mimir refuses long ranges
  (`err-mimir-max-query-length`), so the adapter splits ranges into chunks of this size. Default 720.
- In queries, `$step` is replaced by the bucket length in range queries and by the whole window in
  window queries, so one expression serves both: `sum(increase(x_total[$step]))`.
- Example: requests per team, `sum by (team) (increase(http_requests_total[$step]))`, with
  `"by": "team"`.

### clickhouse

- `source_url` (port 8123, or 8443 with TLS), `source_database`, `source_headers`.
- A query returns one row per bucket and series, with a `t` column (bucket start, unix seconds) and a
  `value` column. Every other column is a label.
- Placeholders: `$bucket(col)`, `$range(col)`, `$start`, `$end`, `$step`.
- Example: orders per region from `orders(ts DateTime, region String)`,
  `SELECT $bucket(ts) AS t, region, count() AS value FROM orders WHERE $range(ts) GROUP BY t, region`,
  with `"by": "region"`.

### command

- The metric's `query` is a shell command, run from `$HOME` with `MM_START`, `MM_END`, `MM_STEP` and
  `MM_WORK` set.
- It prints JSON lines: `{"t": <bucket start>, "value": <number>, "<label>": "..."}`.
- Put the script in `work/sources/`. For example, daily signups per plan from a REST API:

  ```python
  import json, os, urllib.request
  start, end, step = (int(os.environ[k]) for k in ("MM_START", "MM_END", "MM_STEP"))
  url = "https://api.example.com/__platform_conn/CONN_ID/v1/signups"
  with urllib.request.urlopen(f"{url}?from={start}&to={end}&bucket={step}", timeout=60) as r:
      for row in json.load(r)["buckets"]:
          print(json.dumps({"t": row["start"], "value": row["count"], "plan": row["plan"]}))
  ```

  with the metric's `query` set to `python3 "$MM_WORK/sources/signups.py"`.

## Credentials

A credential never goes in `work/CONFIG.md`, a script or a query. The owner adds a **Custom
Header** connection for the source's host in the agent's settings: the header name and value, for
example `Authorization: Bearer ...`, `X-ClickHouse-Key: ...` or `X-API-Key: ...`. The agent's
gateway adds the header on the way out, and the agent never sees the value.

This kit sets `requireConnectionAddress: true`, so the gateway injects a credential only into a
request that names the connection. A Custom Header connection sets no environment variable, so a
request names it through its **path prefix** on the real host:

```
https://<host>/__platform_conn/<connection id>/<the source's own path>
```

The gateway strips the prefix before the request leaves, so the source sees its usual path.
Write `source_url` with the prefix in it. A `command` script puts it in the URLs it calls.
Sources that need no credential (an in-cluster Prometheus, an anonymous tenant) need no
connection and no prefix.

Postgres, BigQuery and other non-HTTP sources can't take an injected header. Reach them
through their HTTP API (BigQuery's REST API, a PostgREST or Hasura endpoint, Snowflake's SQL
API) from a `command` script. Never paste a password into the agent.

## When the source does not answer

Test with the smallest query (`python3 "$HOME/scripts/ask.py" raw 'up'`, or `'SELECT 1'`). Then
work outward:

| Symptom | Usual cause | What to do |
| --- | --- | --- |
| DNS failure | the host is internal-only | use an address the sandbox can resolve; ask the owner |
| connect timeout | a firewall or route drops the sandbox's outgoing IP | `curl -s https://ifconfig.me` shows that IP; the source's network owner must allow it. A connection does not change routing |
| TLS error | self-signed certificate | `source_insecure: 1`, if the owner agrees |
| 401 / 403 | no connection, wrong header, or the prefix is missing from `source_url` | check the connection and the prefix |
| 403 from the gateway | the egress policy blocks the host | the owner adds the host to the agent's egress rules |
| 400 "query too long" | the range is longer than the source allows | lower `max_query_hours` |

Record what you found, and what fixed it, in `work/CLAUDE.md`.

## A new adapter

A source that a `command` script would serve badly (a common one, with its own query language)
gets its own module, `scripts/sources/<name>.py`, with a `Source` class:

```python
class Source:
    name = "<name>"
    def __init__(self, conf): ...                        # conf = work/CONFIG.md as a dict
    def range(self, query, start, end, step):            # -> [{"labels": {...}, "points": [[t, v], ...]}]
        ...                                              # t = bucket start; buckets [start, end)
    def window(self, query, start, end):                 # -> [{"labels": {...}, "value": v}]
        ...                                              # one value per series over the whole window
    def raw(self, query, at):                            # -> anything JSON, for ask.py raw
        ...
```

`window` has to be **independent** of `range`: one query over the whole window, not the
sum of the buckets. That independence is what makes `verify.py` a real cross-check. Use only
the standard library (`scripts/sources/http.py` has a request helper with retries). Add a
`demo`-style offline test in `scripts/tests/`, and its section above.
