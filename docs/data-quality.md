# Data quality: before you trust a number

Read this before you trust a new metric, and whenever a number looks off. Each rule below
comes from a real incident on a production dashboard. Every one of those numbers looked
plausible until it was broken down.

## Break it down by producer first

Before you aggregate anything, count its series by whatever tells producers apart: `job`,
`instance`, `pod`, `namespace`, `replica`, the table's `host` column.

```promql
count by (job, namespace) (my_metric)
```

Look for:

- **Test and canary producers** sharing a namespace or table with production. A test exporter
  with no traffic once reported 100% utilisation and added a flat ~35% to a production average
  for over a week. Fix it with an **allowlist** of producers, not a denylist: a new test
  exporter then can't slip in.
- **HA duplicates**: two replicas of the same scraper both stored (a `replica` label, or none on
  one copy). Filter to one: `{prometheus_replica!~".+-1"}`.
- **Separate engines that look like duplicates**: several series per pod can be real (one per
  data-parallel rank, with its own port or `engine` label). Check before you deduplicate.
- **Role splits**: a system that reports the same thing at two stages (a gateway and a backend,
  prefill and decode) counts it twice if you pool them. Pick one stage.

Write down what you found and what you excluded in `work/CLAUDE.md`, and add a one-line
`notes` entry in `work/metrics.json`.

## Counters across gaps

- `increase()` over a **long** window (a day or more) can count straight across a gap in a
  counter and inflate the total. Hourly buckets, which this kit uses, are safe. Long ad-hoc
  windows in `ask.py raw` are not: sum hourly increases instead.
- A counter that resets (a restart) is handled by `increase()`. A gauge that someone treats as a
  counter is not.

## Time-weighted counts

To count things that come and go (GPUs, pods, users online), weight by time:

```promql
sum_over_time(count(DCGM_FI_DEV_GPU_UTIL)[$step:1m]) / 60      # GPU-hours per hourly bucket
```

`avg_over_time` over a subquery skips the minutes where the count was absent. A pool that exists
for 10 minutes of an hour then reads as if it ran the whole hour. That once showed a 4-GPU
pool as 83 GPUs.

## Values the producer gets wrong

Some producers report impossible values: a saturation of 343%, a negative latency. Cap them per
reading, before averaging, and say so in the metric's description:

```promql
avg(clamp_max(saturation, 1))
```

## Histograms

- Percentiles from a histogram (`histogram_quantile`) are interpolated within a bucket. Say so
  when you quote one.
- "% within target" is exact only when the target is a bucket edge. Check the edges
  (`count by (le) (x_bucket)`). If there is no 30 s bucket, a 30 s target returns nothing.
- Never pool histograms from different stages (see Role splits).

## Gaps and missing history

- Every source has a first sample. Find it (`ask.py raw` on a coarse range) and record it in
  `work/CLAUDE.md`. "All time" means since then, and answers about earlier periods say there
  is no data.
- When a monitoring outage leaves gaps, record them in `notes`. Never fill a gap with zero.
  The page shows a gap as a gap.

## Cross-check with an independent source

Where two systems measure the same thing (a gateway's request count and the backend's, Kubernetes
GPU requests and DCGM's count), compare them once when you add the metric, and again whenever the
number moves unexpectedly. Agreement within about 1% is normal. Record the comparison in
`work/CLAUDE.md`. If it should run every hour, give the metric a `verify_query` that reads the
other system.
