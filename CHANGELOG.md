# Changelog

Each version says what changed and, under **Upgrade:**, what an instance
already running must do to adopt it ([`docs/persistence.md`](docs/persistence.md)
→ **Definition version & upgrade**).

## 0.8.0

- New optional key `owner_slack_id`: the owner's Slack user id. A Slack
  message whose sender is that id, in `slack_channel` or a DM to the bot, has
  the same rights as the direct session: the schedule, the data source,
  sharing, failure reports, `work/CONFIG.md` and the definition. Before, those
  could only be changed in the direct session.
- Only the sender id the platform gives a message counts, never a name or id
  in its text. `owner_slack_id` itself changes only in the direct session.
  The hard invariants still hold for the owner everywhere.
- Onboarding offers the key; `verify-onboarding.sh --config` checks it is a
  Slack user id.

**Upgrade:** nothing to change. Tell the owner they can add
`- owner_slack_id: <their user id>` to `work/CONFIG.md` in the direct session
to change these things from Slack.

## 0.7.1

- A failed hourly refresh DMs `report_to` only when the owner has something
  to do or know: a cause only they can fix (reported on the first failure),
  or 3 hourly runs in a row failed. A failure the agent fixes itself, or an
  upstream cause that clears within 3 runs, posts nothing and is logged in
  `work/logs/refresh.log`. Before, every failed run sent a DM.

**Upgrade:** nothing to change. Tell the owner they will get fewer failure DMs.

## 0.7.0

- Anyone in `slack_channel` who asks the agent can change the dashboard:
  what it measures, hand-set figures (with `set_by`), the layout, and the
  `title`, `subtitle`, `logo` and `logo_dark`. Being in the channel is the
  permission, and the owner controls who is in it. Before, only the owner
  could, unless they listed approvers by Slack user id in `metric_deciders`.
- `metric_deciders` is removed. Onboarding no longer asks for it.
- Unchanged: a Slack message still cannot change the data source, any other
  `work/CONFIG.md` key, sharing, the schedule, the definition or a check, and
  every change still goes live only through a refresh that passes.

**Upgrade:** remove the `- metric_deciders: ...` line from `work/CONFIG.md`,
if it is there (`verify-onboarding.sh --config` now fails on it as an unknown
key). Tell the owner that anyone in the channel can now change the dashboard.

## 0.6.1

- A target, a rate or another hand-set figure asked for in Slack follows the
  same rule as a metric change: only a sender `metric_deciders` allows can
  add it, with `set_by` naming them. Before, `docs/slack.md` let anyone in
  the channel add one, though it lives in `work/metrics.json`.
- `scripts/validate-definition.sh` describes itself, not where it came from.

**Upgrade:** none.

## 0.6.0

- One instance can read more than one source. `source` stays the default;
  the new optional key `sources` adds named ones (`github=command`), each
  with its own keys prefixed by its name (`github_source_url`,
  `github_source_label`). A named source never inherits the default's URL
  or headers.
- A metric reads another source with `"source": "<name>"` in
  `work/metrics.json`. `fetch.py`, `verify.py` and `ask.py` use each
  metric's own source, so every check and cross-check still covers every
  metric. A metric naming a source that `work/CONFIG.md` doesn't have fails
  the refresh.
- `ask.py raw` takes `--source <name>`; `verify-onboarding.sh` checks every
  source's adapter and URL, and `--live` probes each one.
- The page names every source in its header, and with more than one, says
  in **How it is measured** which source each metric comes from.

**Upgrade:** none. An instance with one source works as before, and its
snapshot keeps its history. To add a source, the owner adds `- sources: ...`
to `work/CONFIG.md` in the direct session ([`docs/sources.md`](docs/sources.md)
→ **Several sources**).

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
