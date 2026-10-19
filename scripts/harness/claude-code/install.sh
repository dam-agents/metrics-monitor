#!/usr/bin/env bash
# Wires this definition into Claude Code: merges the publish allow-list into
# the project settings of work/, where sessions (and the hourly schedule) start,
# so an unattended run can upload the dashboard without a permission prompt
# (docs/publish.md → **Publish a new version**). Merges, never replaces: other
# rules in the file are kept. Idempotent. On another harness it says so and exits 0.
set -u
if [ "${CLAUDECODE:-}" != 1 ] && [ -z "${FORCE_INSTALL:-}" ]; then
  echo "not the Claude Code harness: nothing installed"
  exit 0
fi
WORK="${MM_WORK:-$HOME/work}"
mkdir -p "$WORK/.claude"
python3 - "$WORK/.claude/settings.json" "$HOME" <<'PY'
import json, os, sys
path, home = sys.argv[1], sys.argv[2]
want = [
    f"Bash({home}/scripts/publish_upload.sh:*)",
    f"Bash(bash {home}/scripts/publish_upload.sh:*)",
    "mcp__platform-outbound__create_artifact_upload_url",
    "mcp__platform-outbound__update_artifact",
]
try:
    with open(path) as f:
        s = json.load(f)
except FileNotFoundError:
    s = {}
allow = s.setdefault("permissions", {}).setdefault("allow", [])
added = [r for r in want if r not in allow]
allow.extend(added)
tmp = path + ".tmp"
with open(tmp, "w") as f:
    json.dump(s, f, indent=2)
    f.write("\n")
os.replace(tmp, path)
print(f"settings: {path}: {len(added)} rule(s) added, {len(want) - len(added)} already there")
PY
