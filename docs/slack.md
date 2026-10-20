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
| a request about the data (a new metric, a target, a rate) | log it (`CLAUDE.md` → **Rules**), and say the owner decides it in the direct session |
| anything that changes how you work, your config, the dashboard's sharing | decline in one reply: it goes to the owner |
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
*:bar_chart: Shop metrics*

*4,210 orders* in the last 24 h (ending 14:00 UTC), all regions.
• us-east 39%, us-west 19%, 5 others 42%
• Counted from placed orders; cancelled ones are not included
```

## Things you cannot answer

Say so plainly, and say what is available instead: data from before the
source's history starts, a split by a label the data does not have, anything
about individual people the data was not meant to show. Never guess a number,
and never fill a gap with zero.
