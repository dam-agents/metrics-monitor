# Metrics Monitor

A [DAM](https://github.com/dam-agents/dam) starter kit for an agent that keeps one dashboard of
your data current and answers questions about that data.

- **Hourly, checked dashboard.** Every hour the agent pulls your data source into a snapshot,
  checks it, and publishes a new version of one dashboard artifact. The link stays the same.
  A run that fails any check publishes nothing, and the last good version stays live.
- **You choose who sees it.** Private (only you, in the app), public (anyone with the link), or
  restricted (email addresses you name, after sign-in).
- **Q&A in Slack.** Add the agent to a team channel. People ask about the data and get answers
  from a live query, each stating the number with its unit, the exact time window in UTC and the
  scope. When the data cannot answer, the agent says so; it never guesses.
- **Any data source.** Adapters for Prometheus-compatible APIs (Prometheus, Grafana Mimir,
  Thanos, VictoriaMetrics) and ClickHouse. A `command` adapter covers anything a script can read
  (Postgres, BigQuery, a REST API). Adding an adapter takes one small Python class.

## How a run works

```
fetch.py ─► check_snapshot.py ─► build.py ─► verify.py ─► browser check ─► publish
 source       fresh? complete?    snapshot    each number    no errors,      new artifact
 → snapshot   history intact?     → page      vs an inde-    no NaN in any   version, same
              series all there?               pendent query  range           link
```

`scripts/refresh.sh` runs the first five steps and exits non-zero at the first failure. It then
puts the previous snapshot back, so what is on disk matches what is live. The agent publishes
only after an exit 0. If a run fails, the agent works out why. It may fix its own tooling, but it
may not loosen a check. It reports once, by Slack DM, to the person named at setup. When a run
succeeds, it posts nothing.

## The checks

| Check | Fails when |
| --- | --- |
| freshness | the data ends more than `max_lag_hours` ago, or no metric has data in `expect_activity_hours` |
| completeness | history now starts later, a series active last week is gone, or a total that was already published fell by more than 0.5% |
| cross-check | the dashboard's 7-day value of any metric differs from an independent query over the whole window by more than its tolerance (default 1%) |
| browser | the page throws, shows NaN / undefined, or draws no chart, in any range, in light or dark |

These rules come from running a production LLM-serving dashboard. Each one was added after a
number that looked plausible turned out to be wrong: a test exporter inflating an average, a
duplicate HA replica, a counter counted across a gap, a pool counted as present while it was
gone. [`docs/data-quality.md`](docs/data-quality.md) collects them.

## Create an agent

The kit is not in the DAM catalog yet. To try it, create an agent from this repository's
`kit.yaml` (a starter kit whose `seed` is this repository). On first run, the agent onboards you
([`ONBOARDING.md`](ONBOARDING.md)):

1. **Source.** Which system, its URL, and a credential if it needs one. Add the credential as a
   **Custom Header** connection in the agent's settings. The gateway adds the header to each
   request, and the agent never sees it.
2. **Metrics.** You and the agent go through what exists and agree, metric by metric, what to
   measure. It goes in `work/metrics.json` ([`docs/metrics.md`](docs/metrics.md)). Targets and
   rates come only from you, each recorded with who set it.
3. **Dashboard.** A title, and who may see it.
4. **Slack.** The team channel, an optional header line for messages, and who gets failure DMs.
5. **First refresh.** The agent pulls the full history, runs every check, shows you the page,
   and publishes it. The hourly schedule starts after that.

Want to see it before connecting real data? Choose the `demo` source: synthetic data that runs
the whole loop.

## What it needs

| | |
| --- | --- |
| Harness | Claude Code. The unattended publish uses its permission allow-list ([`docs/publish.md`](docs/publish.md)) |
| Connections | optional: a Custom Header connection for the data source; optional: GitHub (read), to check for updates |
| Channel | optional: Slack, bound to the team channel. Turn on ambient mode for read-along answers |
| Egress | `all` by default, since data sources live anywhere. Narrow it to your source's host after creating the agent |
| Schedule | `metrics-monitor-refresh-hourly`, cron `0 * * * *` UTC, a fresh session each run |

## Layout

```
kit.yaml                    the starter kit: seed, install, connections, channel, schedule
CLAUDE.md                   the operating manual: the hourly run, answering, rules, invariants
ONBOARDING.md               first-run intake
docs/                       publish, failures, slack, sources, metrics, data quality, persistence
scripts/refresh.sh          fetch → check → build → verify → browser, logs every run
scripts/fetch.py            source → work/data/snapshot.json (incremental)
scripts/check_snapshot.py   freshness and completeness vs the previous snapshot
scripts/verify.py           every metric vs an independent window query
scripts/build.py            dashboard/template.html + snapshot → work/dist/dashboard.html
scripts/ask.py              live answers: ask.py list | <metric> --since 24h | raw '<query>'
scripts/publish_upload.sh   the one upload path to the artifact store
scripts/sources/            adapters: prometheus, clickhouse, command, demo
scripts/browser/            headless render check and screenshots (playwright-core)
dashboard/template.html     the self-contained page, light and dark
examples/                   metrics.json starting points per source
```

Everything an instance owns lives in `work/`, which is never tracked: its config, metrics,
snapshot, logs, built page and its own notes ([`docs/persistence.md`](docs/persistence.md)).

## Develop

```sh
bash scripts/tests/run.sh               # offline: the demo source end to end, validation, config parity
bash scripts/validate-definition.sh .   # the definition's structure
```

To try the pipeline by hand without an agent:

```sh
mkdir -p /tmp/mmw && cp examples/demo/metrics.json /tmp/mmw/
printf -- '- source: demo\n- title: Demo\n- visibility: private\n' > /tmp/mmw/CONFIG.md
(cd scripts/browser && npm ci)
MM_WORK=/tmp/mmw MM_NO_WAIT=1 bash scripts/refresh.sh
open /tmp/mmw/dist/dashboard.html
```

## License

Apache 2.0, see [`LICENSE`](LICENSE).
