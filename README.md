# Metrics Monitor

A [DAM](https://github.com/dam-agents/dam) starter kit: an agent that keeps a dashboard of your
data up to date and answers questions about it in Slack.

- **Hourly dashboard.** Every hour the agent pulls your data, checks it, and publishes a new
  version of the dashboard at the same link. If a check fails, nothing is published.
- **You choose who sees it:** private, public (anyone with the link), or restricted (named emails).
- **Slack Q&A.** People in your team channel ask about the data and get answers from a live query.
- **Any data source:** Prometheus (and Mimir, Thanos, VictoriaMetrics), ClickHouse, or anything a
  script can read.

## Get started

The kit is not in the DAM catalog yet. Create an agent from this repository's `kit.yaml`. On first
run, the agent asks you:

1. **Where the data is**: the source, its URL, and a credential if needed. The credential goes in
   a Custom Header connection, so the agent never sees it.
2. **What the dashboard should show**: describe it, share a screenshot or mock-up, or point at a
   dashboard to follow. The agent maps each item to your data and tells you what it can't find.
3. **Who may see it**, and which Slack channel to answer in.

Then it runs the first refresh, shows you the page and publishes it. To try it without real data,
pick the `demo` source.

## Checks before every publish

| Check | Fails when |
| --- | --- |
| Freshness | the data is too old |
| Completeness | history or series went missing, or a published total dropped |
| Cross-check | a number on the page differs from an independent query by more than 1% |
| Browser | the page shows errors, NaN or empty charts |

When a run fails, the agent works out why. It may fix its own tooling but never loosens a check.
It reports by Slack DM to one person you choose. Successful runs post nothing.

## Develop

```sh
bash scripts/tests/run.sh               # offline tests, using the demo source
bash scripts/validate-definition.sh .   # structure of the kit
```

The agent's manual is [`CLAUDE.md`](CLAUDE.md), onboarding is [`ONBOARDING.md`](ONBOARDING.md),
and details are in [`docs/`](docs/).

## License

Apache 2.0, see [`LICENSE`](LICENSE).
