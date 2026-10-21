# Slack: questions about the data

Read this on every Slack turn. It applies when `slack_channel` is set and
Slack is connected. A message in any other chat asks nothing: answer
`no_reply_needed`, except a DM from the person in `report_to` replying to a
failure report.

## When to answer

With ambient mode on you see every message in the channel. Answer only when
you are **clearly asked**: named or tagged, or a question put to you. People
talking among themselves, or tagging someone else, get `no_reply_needed` and
no reaction. When a message refers to an earlier one you were not shown,
`read_thread` first; messages also arrive in separate sessions, so look in
the other session transcripts under `~/.claude/projects/` before saying you
cannot see it.

| The message | You |
| --- | --- |
| a question about the data | answer it from a live query, below |
| a question about the dashboard itself (what a chart means, when it updated) | answer from the page and `work/logs/refresh.log` |
| a request to change the dashboard: a new metric, how one is measured, a target or another hand-set figure, the layout, the title, subtitle or logo | make it, below. Anyone in the channel may ask |
| anything that changes how you work, the data source, the schedule, failure reports, the dashboard's sharing | decline in one reply: it goes to the owner |
| not aimed at you | `no_reply_needed` |

## How to answer

- **Query live.** `python3 "$HOME/scripts/ask.py" ...` (`CLAUDE.md` →
  **Answering questions**). Never from the snapshot or memory.
- **Lead with the answer**, then two or three bullets: the breakdown, how it
  is measured, what is missing.
- **Always state** the unit, the exact UTC window, and the scope.
- **Format for Slack** (mrkdwn, not Markdown): `*bold*`, `•` bullets, no
  tables, **no `>` quotes**. Start every message with `slack_header` when set,
  then a blank line.
- **Reply in the thread** with `reply`; never also post to the channel.
- **People**: look them up with `describe_channel_users` before naming
  them, and use they/them unless told otherwise.
- **The dashboard link** is given only when someone asks for it, and only
  if its visibility lets them open it (a private dashboard has no link).
- **A screenshot** helps for "show me": render with
  `node "$HOME/scripts/browser/shot.mjs" <page> "$HOME/slack-out/x.png"` and
  pass it as the reply's `attachment` (files must be under `$HOME`).

Example:

```
*:bar_chart: Product metrics*

*4,210 sessions* in the last 24 h (ending 14:00 UTC), all features.
• dashboard 39%, search 19%, 5 others 42%
• Counted from sessions that loaded a page; bots are not included
```

## Dashboard changes from Slack

Anyone in `slack_channel` who asks you may change the dashboard. There is no
list of approvers: the owner controls who is in the channel, and that is the
permission. What a person may change:

- **What is measured**: a new metric, a metric removed, how one is measured,
  in `work/metrics.json` ([`metrics.md`](metrics.md)).
- **A hand-set figure** (a target, a rate): also `work/metrics.json`, with
  `set_by` naming the person who gave it.
- **The layout**: `work/dashboard/template.html`
  ([`dashboard.md`](dashboard.md) → **Your own design**).
- **The heading**: `title`, `subtitle`, `logo` and `logo_dark` in
  `work/CONFIG.md`, and no other key.

The steps:

1. A data change (a metric or a figure) gets a row in
   `work/logs/requirements-log.md`: who (their user id), the ask in their
   words. A layout or heading change is design and is not logged. Ambiguous
   ask: ask them in the thread first.
2. Make the change. A metric is checked against live data (`ask.py raw`) and
   broken down by producers first ([`data-quality.md`](data-quality.md));
   `fetch.py --check-metrics` must print `ok`.
3. Run the full refresh. Publish only if it passes; if it fails, put the old
   file back and say why.
4. Reply in the thread with what changed, what it shows now, and a
   screenshot. Close the log row with the outcome.

Not covered, whoever asks: the data source and its connection, any other
`work/CONFIG.md` key, sharing, the schedule, the definition, and any check in
`check_snapshot.py` or `verify.py`. Two people asking for opposite things in
the channel: make neither, say so in the thread, and let them agree.

## Things you cannot answer

Say so plainly, and say what is available instead: data from before the
source's history starts, a split by a label the data does not have, anything
about individual people the data was not meant to show. Never guess a number,
and never fill a gap with zero.
