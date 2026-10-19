# Metrics Monitor

A [DAM](https://github.com/dam-agents/dam) starter kit: an agent that keeps a dashboard of your
data up to date and answers questions about it in Slack.

- **Hourly dashboard.** Every hour the agent pulls your data, checks it, and publishes a new
  version of the dashboard at the same link. If a check fails, nothing is published.
- **You choose who sees it:** private, public (anyone with the link), or restricted (named emails).
- **Slack Q&A.** People in your team channel ask about the data and get answers from a live query.
- **Any data source:** Prometheus (and Mimir, Thanos, VictoriaMetrics), ClickHouse, or anything a
  script can read.

## Use it today

The kit is not in the DAM catalog yet, so it isn't under **Browse starter kits**. There are two ways
to use it now.

### Option A: ask your DAM admin to list it (one click for everyone)

An admin adds this repository to a catalog the install reads, such as the install's own catalog
or a team catalog repository:

```yaml
# catalog.yaml
kits:
  - url: https://github.com/dam-agents/metrics-monitor
```

It appears under **Browse starter kits** at the catalog's next refresh, with no redeploy. Then
choose **Metrics Monitor**, connect Slack if you want Q&A, and create the agent. Onboarding
starts by itself, and the hourly schedule starts when it finishes.

### Option B: set it up by hand (works on any DAM today)

1. **Create an agent** on the **Claude Code** harness.
2. **Let it reach your data.** In the agent's settings, under egress, allow your source's host.
   Skip this for the `demo` source.
3. **Add the credential, if your source needs one.** Add a **Custom Header** connection for the
   source's host, for example `Authorization: Bearer …` or `X-ClickHouse-Key: …`. Note its id;
   the agent asks for it.
4. **Optional: bind a Slack channel** to the agent, so the team can ask questions. Turn on
   ambient mode if it should read along and answer only when asked.
5. **Send the agent this message:**

   ```text
   Install the Metrics Monitor starter kit into your home directory, then onboard me:
   cd "$HOME" && git init -q && git remote add origin https://github.com/dam-agents/metrics-monitor
   git fetch -q origin main && git checkout -q -f -B main origin/main
   cd "$HOME/scripts/browser" && npm ci --no-audit --no-fund --silent
   Then read $HOME/CLAUDE.md and follow $HOME/ONBOARDING.md. I set this up by hand,
   so create the hourly schedule at the end yourself.
   ```

The checkout adds the kit's files to the agent's home and leaves everything already there in
place. The agent then onboards you, and asks:

1. **Where the data is**: the source, its URL, and the connection id from step 3.
2. **What the dashboard should show**: describe it, share a screenshot or mock-up, or point at a
   dashboard to follow. The agent maps each item to your data and tells you what it can't find.
3. **Who may see it**, an optional logo, the Slack channel, and who gets a DM when a run fails.

Then it runs the first refresh, shows you the page, publishes it and creates the hourly schedule.
To try it without real data, pick the `demo` source.

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
