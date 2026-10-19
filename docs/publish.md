# Publishing the dashboard

Read this on every publish and for any question about who can see the
dashboard. The dashboard is one artifact; every publish is a new version
of it, so its link never changes.

## Who can see it

An artifact's visibility is one of three, and the owner chooses it
(`visibility` in `work/CONFIG.md` records the choice):

| Visibility | Who opens the link | Who sets it |
| --- | --- | --- |
| `private` | the owner, in the app; no link | default |
| `public` | anyone holding the link, no sign-in | you, with `set_artifact_sharing`, only when the owner asks in the direct session |
| `restricted` | the owner and the email addresses they list, after sign-in | **only the owner**, in the artifact's **Share** dialog |

Your tools offer only private and public, and they refuse any sharing change
on an artifact that is already restricted. So you never widen a restricted
link, and never edit who is on it. Asked to share it with named people: tell
the person to open the artifact, choose **Share**, pick restricted and add
the addresses. Every publish goes live to whoever the link reaches; that is
the reason a failed refresh is never published.

A restricted share does not carry the viewer to another artifact, so the
page links to no other artifact: anything it shows is embedded in it.

## Publish a new version

After `scripts/refresh.sh` exits 0, three steps, each on its own:

1. `create_artifact_upload_url` with `file_name: dashboard.html`. It returns a
   presigned `url` and an `upload_ref`.
2. `/home/agent/scripts/publish_upload.sh '<url>'` (the literal path, not
   `$HOME`), **as a command of its own**: no `cd`, `&&`, pipes or redirections. It PUTs
   `work/dist/dashboard.html` with `Content-Type: text/html; charset=utf-8`
   (without it the artifact store keeps the page as form data), only to the
   platform's artifact store, with retries.
3. `update_artifact` with `id: <artifact_id>` and `upload_ref`. It returns the
   new version number.

Then record it: append `published v<N>` to the last line of
`work/logs/refresh.log`, and add the version to `work/artifacts.json`
(`{"dashboard": {"id", "title", "version", "published_at"}}`).

**Why a script, not curl:** an unattended run cannot answer a permission
prompt. `work/.claude/settings.json` (written by
`scripts/harness/claude-code/install.sh` at onboarding) allow-lists exactly
this script and the two artifact tools, so the hourly run never stops to ask, and the
auto-mode permission check does not have to judge a raw upload (it has
refused raw curl uploads before, then refused retries). Keep the script the
only upload path. Do not add a broader allow rule.

## First publish

During onboarding, with no `artifact_id` yet:

1. Steps 1 and 2 above.
2. `create_artifact` with `title: <title>`, `upload_ref`, `type: html`,
   `source_path: work/dist/dashboard.html`. Leave `visibility` out (private).
3. Write the returned id to `work/CONFIG.md` as `- artifact_id: <id>` and
   start `work/artifacts.json`.
4. Apply `visibility` (`ONBOARDING.md` → **4. First refresh and publish**).

## When a publish fails

- `publish_upload.sh` exits non-zero after three attempts: run steps 1-3 once
  more with a fresh URL (presigned URLs expire). Still failing: report it as
  a failure (`CLAUDE.md` → **The hourly run**); the data is fine, only the
  upload is not.
- `update_artifact` refuses the artifact (deleted, not found): never create a
  new one unattended, since its link would differ. Report it; in the direct
  session, ask the owner whether to create a new artifact.
- A permission prompt or refusal on the script: the allow-list in
  `work/.claude/settings.json` is missing or changed: run
  `bash "$HOME/scripts/harness/claude-code/install.sh"` and retry once.
  Still refused: report it; never upload another way.
