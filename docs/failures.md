# When a refresh fails

Read this when `scripts/refresh.sh` exits non-zero. The previous snapshot is
already back in place and rebuilt, so `work/` matches what is live, and
nothing was published.

## 1. Find what failed

The last line of `work/logs/refresh.log` names the step and the exit code;
the run's full output is the file it names under `work/logs/runs/`.

| Exit | Step | Means |
| --- | --- | --- |
| 1 | fetch or build | the source did not answer, a query failed, or a script broke |
| 4 | freshness | `check_snapshot.py`: data is late, missing, or history changed |
| 2 | verify | `verify.py`: a dashboard number disagrees with an independent query |
| 3 | browser | the page threw an error or rendered NaN / undefined |

## 2. Fix what you may

You may fix, without asking:

- **Tooling**: a script bug, a browser that would not start, a dependency
  (`cd "$HOME/scripts/browser" && npm ci`). A fix to the definition goes
  through [self-modification.md](self-modification.md); a fix to
  `work/` only is fine.
- **A known kind of artefact series**: a series of the same kind you
  already excluded once and recorded in `work/CLAUDE.md` (a canary or test
  exporter, an HA replica's duplicate). Exclude it in the metric's query, say
  so in `work/CLAUDE.md`, and log it in the requirements log, since it changes
  what is measured.
- **A source that is briefly unavailable** (5xx, timeout): wait a minute and
  re-run once.

You may **never**: loosen, skip or work around a check; change a tolerance,
a KPI, a rate, what a metric means, the schedule, the design or your
permissions; or publish anything the checks did not pass. Those need the
owner to ask: in the direct session, or as `owner_slack_id` in Slack.

After any fix, re-run the **whole** `bash "$HOME/scripts/refresh.sh"`, never a
single step, and publish only if it exits 0.

## 3. Common causes

- **Data ends too early** (`data ends ... h ago`): the source stopped
  receiving data, or its ingestion is behind. Query the newest value directly
  (`ask.py raw`). Not yours to fix: report it.
- **No activity** in `expect_activity_hours`: real silence (a quiet weekend)
  or a broken producer. Check the producers' own liveness (`up` in
  Prometheus). If quiet periods are normal, the person can raise
  `expect_activity_hours` in `work/metrics.json`; you do not.
- **Series gone**: a label value that had data in the last week vanished.
  Renamed (a pod or namespace changed) or really gone. Report which.
- **Total fell**: history that was already published shrank. The source lost
  data, retention cut it, or the query changed meaning. Never publish over it.
- **Verify mismatch**: break both queries down by producer
  ([data-quality.md](data-quality.md)). A new exporter, a duplicate replica,
  or a counter reset across a gap is the usual cause.
- **Browser check**: run `node "$HOME/scripts/browser/check.mjs"
  "$HOME/work/dist/dashboard.html"` and read its errors; a new metric with an
  unexpected shape (no data at all, a label with no value) is the usual cause.

## 4. Report only what needs the owner

The owner hears about a failure only when they have something to do or know.
Everything else stays in `work/logs/refresh.log`.

- **You fixed it** and the re-run passed and published: post nothing. Add a
  `fixed: <what>` note to the log line.
- **A cause outside you that should clear on its own** (the source briefly
  unavailable, an upstream answering partly, ingestion behind): post nothing.
  Log `waiting: <cause>` and let the next hourly runs try again. Report it
  only when **3 hourly runs in a row** have failed (count the trailing
  `FAILED` lines in `work/logs/refresh.log`), because the live dashboard is
  then hours behind.
- **Anything only the owner can fix** (history that shrank, a check that
  looks wrong, a metric whose meaning changed, a credential or connection
  that stopped working): report on the first failure.

A report is one DM to `report_to` with `send_channel_message` (`channel: slack`,
`chatId: <report_to>`), never a channel post, starting with `slack_header` when set:

- what failed (step, the check's own line),
- what you did about it, and why you could not fix it,
- what the owner needs to do, or that nothing is needed and you will keep trying,
- what is live now (the version and the data's end time).

A failure you already reported, with the same cause, is not reported again or
retried until something changes; the log line says `known: <cause>`. When a
reported failure clears, one short DM says so. A failure that was never
reported clears silently. On success, post nothing.
