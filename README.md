# Metrics Monitor

A [DAM](https://github.com/dam-agents/dam) starter kit: an agent that keeps a dashboard of your
data up to date and answers questions about it in Slack.

- **Hourly dashboard.** Every hour, at :00 UTC, the agent pulls your data, checks it, and
  publishes a new version of the dashboard at the same link. If a check fails, nothing is
  published.
- **You choose who sees it:** private, public (anyone with the link), or restricted (named emails).
- **Slack Q&A.** People in your team channel ask about the data and get answers from a live query.
- **Any data source:** Prometheus (and Mimir, Thanos, VictoriaMetrics), ClickHouse, or anything a
  script can read.

## Set it up

1. **Create an agent from the kit.** In DAM, open **Starter kits** → **Knowledge** →
   **Metrics Monitor**. It runs on the **Claude Code** harness.
2. **Let it reach your data.** The kit starts with egress open to all hosts; narrow it to your
   source's host in the agent's settings. Skip this for the `demo` source.
3. **Add the credential, if your source needs one.** Add a **Custom Header** connection for the
   source's host, for example `Authorization: Bearer …` or `X-ClickHouse-Key: …`. Note its id;
   the agent asks for it.
4. **Optional: bind a Slack channel** to the agent, so the team can ask questions. Turn on
   ambient mode if it should read along and answer only when asked.

The agent then onboards you, and asks:

1. **Where the data is**: the source, its URL, and the connection id from step 3.
2. **What the dashboard should show**: describe it, share a screenshot or mock-up, or point at a
   dashboard to follow. The agent maps each item to your data and tells you what it can't find.
3. **Who may see it**, an optional logo, the Slack channel, and who gets a DM when a run fails.

Then it runs the first refresh, shows you the page and publishes it. The hourly schedule starts
when onboarding is done. To try it without real data, pick the `demo` source: a synthetic software
product with sessions per feature, page load time, signups and new revenue.

Optional: add a **GitHub** connection with read access to this repository. The agent then checks
for newer versions of itself and proposes upgrades as a patch. It never needs write access.

### Without the starter kit

On a DAM whose catalog does not list this kit, create a Claude Code agent, do steps 2 to 4, and
send it this message:

```text
Install the Metrics Monitor starter kit into your home directory with the commands below,
then read $HOME/CLAUDE.md and follow $HOME/ONBOARDING.md. I set this up by hand, so create
the hourly schedule at the end yourself. If the checkout stops because a file is in the way,
tell me which files and stop.

cd "$HOME" && git init -q
git remote get-url origin >/dev/null 2>&1 || git remote add origin https://github.com/dam-agents/metrics-monitor
git fetch -q origin main && git checkout -q -B main origin/main
cd "$HOME/scripts/browser" && npm ci --no-audit --no-fund --silent
```

The checkout adds the kit's files to the agent's home and leaves your other files in place. It
never overwrites a file: if a file with the same name as a kit file is already there, the
checkout stops and the agent tells you which one.

### Who can see the dashboard

| Choice | Who sees it | Who sets it |
| --- | --- | --- |
| Private | only you, in DAM | default |
| Public | anyone with the link | the agent, when you choose it |
| Restricted | email addresses you name, after sign-in | you, in the artifact's **Share** dialog |

## Checks before every publish

| Check | Fails when |
| --- | --- |
| Freshness | the data is too old |
| Completeness | history or series went missing, or a published total dropped by more than 0.5% |
| Cross-check | a number on the page differs from an independent query by more than 1% |
| Browser | the page shows errors or NaN, or has no charts |

When a run fails, the agent works out why. It may fix its own tooling but never loosens a check.
It reports by Slack DM to one person you choose. Successful runs post nothing.

## Develop

You need Python 3.12 and Node 22. The browser check also needs `scripts/browser/node_modules` and
a headless Chromium (or `MM_CHROMIUM` set to one); without `node_modules`, the tests skip it.

```sh
(cd scripts/browser && npm ci && npx playwright-core install chromium-headless-shell)
bash scripts/tests/run.sh               # offline tests, using the demo source
bash scripts/validate-definition.sh .   # structure of the kit
```

The agent's manual is [`CLAUDE.md`](CLAUDE.md), onboarding is [`ONBOARDING.md`](ONBOARDING.md),
and details are in [`docs/`](docs/).

## License

Apache 2.0, see [`LICENSE`](LICENSE).
