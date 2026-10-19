# Changelog

Each version says what changed and, under **Upgrade:**, what an instance
already running must do to adopt it ([`docs/persistence.md`](docs/persistence.md)
→ **Definition version & upgrade**).

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
