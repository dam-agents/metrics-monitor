# `work/metrics.json`

The file that says what is measured. It belongs to this instance and is
written with the person during onboarding. Changes to it go in the
requirements log. `python3 "$HOME/scripts/fetch.py" --check-metrics` checks it.
`examples/*/metrics.json` are starting points.

## Top level

| Key | Default | Meaning |
| --- | --- | --- |
| `step` | 3600 | bucket length in seconds; the dashboard groups buckets into hours, days or weeks |
| `history_days` | 90 | how far back the first pull reaches |
| `refetch_hours` | 48 | how much recent data each hourly pull fetches again (late data, counters that settle) |
| `max_lag_hours` | 2 | freshness: the data must end at most this long before now |
| `expect_activity_hours` | 6 | at least one metric must have data this recently |
| `notes` | `[]` | sentences shown under "How it is measured" (known gaps, exclusions) |
| `metrics` | | the measured metrics, below |
| `derived` | `[]` | metrics computed from others, below |

## A metric

```json
{
  "id": "requests",
  "label": "Requests served",
  "unit": "requests",
  "kind": "sum",
  "by": "team",
  "query": "sum by (team) (increase(requests_total[$step]))",
  "description": "Requests that completed, per team",
  "kpi": {"op": ">=", "target": 100000, "per": "day", "set_by": "Alex, 2026-10-02"}
}
```

- `id`: lowercase, stable. It keys the snapshot, so renaming it re-pulls the full history.
- `label`, `unit`, `description`: written for the reader. Plain words, no jargon in the label.
- `kind`: how buckets add up over a range:
  - `sum`: a count or total per bucket (requests, tokens, GPU-hours, spend). The range value is the sum.
  - `avg`: a level (latency, utilisation, queue depth). The range value is the mean of the buckets that have data.
  - `last`: a state (users, capacity). The range value is the last bucket.
- `combine`: how series in one bucket add up for "all": `sum` (default for `sum`), `mean`
  (default otherwise) or `max`.
- `by`: the label that splits the query's series (team, model, region). Leave it out when the
  query returns one series. Several series without `by` is an error, so nothing is summed by
  accident. The page colours the top 5 series and folds the rest into "Other".
- `query`: in the source's language ([sources.md](sources.md)).
- `verify_query`: an independent query for the cross-check. Without it, a `sum` metric is checked
  with its own query over the whole window. An `avg` or `last` metric without one is not checked,
  and `verify.py` says so. Leave it out when no independent query gives the same number (a mean of
  hourly medians is not the median of the window).
- `tolerance_pct`: the cross-check tolerance, default 1. Raise it only with the person, and log it.
- `decimals`: fixed decimals on the page (e.g. 1 for a percentage near a target).
- `kpi`: optional, only when the person asks for a target. `op` is `>=` or `<=`. `per: day` scales the target with the range (a daily
  target × 7 for 7 days); `range` (default) compares as is. `set_by` says who set it and when.
  A KPI comes from a person, never from you.

## Derived metrics

Computed on the page from measured metrics, so they always match what is shown.

```json
{"id": "cost", "label": "Compute cost", "unit": "$", "op": "times", "a": "gpu_hours", "factor": 3.0,
 "set_by": "Alex, 2026-10-02: $3 per GPU-hour; set by hand, not measured"}
{"id": "err_rate", "label": "Error rate", "unit": "%", "op": "ratio", "a": "errors", "b": "requests", "factor": 100}
```

- `times`: `a` × `factor`. `a` must be a `sum` metric: multiply GPU-hours by a rate, not GPUs.
  A `times` factor is a hand-set rate, so `set_by` is required and the page labels it.
- `ratio`: `a` ÷ `b` × `factor` (default 1), over the same range.

## Changing a metric

- **Query changed or metric added**: the next refresh pulls that metric's full history, and the
  completeness check skips it once (`WARN ... changed query`).
- **Metric removed**: its series leave the snapshot on the next refresh.
- **`step` changed**: a full re-pull of everything.
- Each of these is a data decision: log it in `work/logs/requirements-log.md` and note it in
  `work/CLAUDE.md`.

## The page

`dashboard/template.html` renders any `metrics.json`:

- **KPIs** first, each ✓ or ✕ with a label.
- **At a glance**: every metric over the range, with the change vs the previous range of the same length.
- **Over time**: one chart per metric. Stacked bars for sums, lines for levels, and a dashed
  line at a KPI target.
- **How it is measured**: definitions, notes and hand-set rates.

An instance with its own design (from a person's mock-up or an existing dashboard) uses
`work/dashboard/template.html` instead: [dashboard.md](dashboard.md) → **Your own design**.
