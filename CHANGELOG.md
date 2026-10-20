# Changelog

Each version says what changed and, under **Upgrade:**, what an instance
already running must do to adopt it ([`docs/persistence.md`](docs/persistence.md)
→ **Definition version & upgrade**).

## 0.5.0

- New optional key `metric_deciders`: who in `slack_channel` may decide a
  change to `work/metrics.json` (a new metric, or how one is measured),
  `channel` or Slack user ids. The agent then makes the change from Slack,
  logs who decided it, and publishes it only through a passing refresh.
  Without the key nothing changes: only the owner decides, in the direct session.
- The hard invariant on Slack messages no longer names `work/metrics.json`;
  a separate invariant covers it, open only to `metric_deciders`, which a
  Slack message can never set. `CONFIG.md`, sharing, the schedule, the
  definition and the checks stay owner-only.

**Upgrade:** none. To allow it, the owner adds `- metric_deciders: ...` to
`work/CONFIG.md` in the direct session.

## 0.4.1

- The demo's Sessions KPI target is 4,500 a day, not 5,000. The demo
  produces just under 5,000 sessions a day, so the first demo dashboard
  showed the KPI off target.

**Upgrade:** none. A running instance keeps its own `work/metrics.json`.

## 0.4.0

- The `demo` source is a synthetic software product: sessions per feature,
  median page load, signups per plan, error hours, and new monthly revenue
  from a hand-set rate per signup. It no longer looks like a model-serving cluster.
- One example, `examples/demo/metrics.json`. The Prometheus, ClickHouse and
  command examples are gone; [`docs/sources.md`](docs/sources.md) has a short
  query for each source instead, and onboarding builds `work/metrics.json`
  from what the person wants to see.
- Docs examples use generic metrics (requests, signups, server-hours) in place
  of GPUs and tokens.
- README → **Set it up** starts from the starter kit in the DAM catalog; the
  hand install is under **Without the starter kit**.
- The kit starts on **Trusted defaults** egress, not all hosts. Onboarding
  names the source's host and the owner allows that one host.

**Upgrade:** a running instance keeps its egress rules; if it was created
with all hosts open, the owner can switch to Trusted defaults and add the
source's host. A running instance keeps its own `work/metrics.json`. An
instance on the `demo` source picks up the new metrics on its next refresh,
which pulls their full history once.

## 0.3.2

- README → **Set it up** is the one way to use the kit today: the catalog
  option is gone. The install message no longer forces the checkout, so it
  stops instead of overwriting a file already in `$HOME`, and it works when
  `$HOME` already has an `origin` remote.
- README: a screenshot of the demo dashboard, the :00 UTC schedule, the
  optional GitHub connection, the 0.5% completeness threshold, what the
  browser check fails on, and what **Develop** needs installed.

**Upgrade:** none.

## 0.3.1

- README → **Use it today**: how to use the kit before it is in a catalog,
  either listed by an admin or set up by hand on any DAM.
- ONBOARDING.md handles a hand-set-up agent: no onboarding tools, and it
  creates the hourly schedule itself at the end.

**Upgrade:** none.

## 0.3.0

- An optional logo beside the dashboard's title: `logo` (and `logo_dark` for
  the dark theme) in `work/CONFIG.md` name an image in `work/` (PNG, JPEG,
  WebP or SVG, under 512 KB). `build.py` embeds it, so the page stays
  self-contained; `verify-onboarding.sh` checks it.

**Upgrade:** none. Without `logo` the page looks as before. An instance with
its own template adds `/*__LOGO__*/null` to show a logo.

## 0.2.0

- Onboarding starts from what the person wants the dashboard to show: a
  description, a screenshot or mock-up, or an existing dashboard to follow.
  New [`docs/dashboard.md`](docs/dashboard.md): map each element to the
  source, say plainly what is not there, and rebuild the reference's layout
  as the instance's own template.
- Targets and rates are no longer prompted for: a figure that is not measured
  appears only when the person gives it. The Prometheus and ClickHouse
  examples no longer carry placeholder targets.

**Upgrade:** none. Instances already running keep their `metrics.json` and
template; `work/reference/` is optional.

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
