# Changelog

Each version says what changed and, under **Upgrade:**, what an instance
already running must do to adopt it ([`docs/persistence.md`](docs/persistence.md)
→ **Definition version & upgrade**).

## 0.1.0

First release.

- Hourly refresh of one data source into a dashboard artifact, published only
  when freshness, completeness, cross-check and browser checks pass.
- Adapters: `prometheus` (Prometheus, Mimir, Thanos, VictoriaMetrics),
  `clickhouse`, `command` (any script), `demo` (synthetic).
- Source-agnostic `work/metrics.json`: sums, levels and states, series split
  by a label, KPIs with who set them, derived metrics and hand-set rates.
- A self-contained dashboard template, light and dark.
- Live answers in Slack and chat (`scripts/ask.py`), with unit, UTC window and scope.
- Failure reports by DM to one person; nothing posted on success.

**Upgrade:** none: a new instance onboards.
