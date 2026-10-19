#!/usr/bin/env bash
# verify-onboarding.sh: does this instance have the shape onboarding promises?
#
# It never repairs: every FAIL carries the fix, and the caller runs it again
# until it prints PASS.
#
#   --config   work/CONFIG.md and work/metrics.json only, mid-onboarding
#   (none)     that, plus the definition checkout and work/
#   --live     all of that, plus: the source answers, a refresh has passed,
#              and the dashboard was published
#
# CONFIG.md is read by scripts/lib/mm.py alone (cfg_all), the same reader the
# pipeline uses, so the two can never disagree. Exit 0 iff nothing FAILed.
set -u
export LC_ALL=C

LIVE=0; STRUCTURE=1
case "${1:-}" in
  --live) LIVE=1 ;;
  --config) STRUCTURE=0 ;;
  '') ;;
  *) echo "usage: $0 [--config|--live]" >&2; exit 2 ;;
esac

DEF="$(cd "$(dirname "$0")/.." && pwd)"
WORK="${MM_WORK:-$HOME/work}"
export MM_WORK="$WORK"
CONFIG="$WORK/CONFIG.md"
KNOWN="source source_url source_headers source_database source_insecure max_query_hours command_timeout source_label title subtitle visibility artifact_id report_to slack_channel slack_header timezone"
REQUIRED="source title visibility"

CHECKS=0; FAILS=0; WARNS=0
ok()   { CHECKS=$((CHECKS + 1)); printf 'ok   %s: %s\n' "$1" "$2"; }
fail() { CHECKS=$((CHECKS + 1)); FAILS=$((FAILS + 1)); printf 'FAIL %s: %s: fix: %s\n' "$1" "$2" "$3"; }
warn() { WARNS=$((WARNS + 1)); printf 'warn %s: %s\n' "$1" "$2"; }

# cfg <key>: through the pipeline's own reader
cfg() { python3 -c 'import sys; sys.path.insert(0, sys.argv[1]); from lib.mm import cfg_all; print(cfg_all().get(sys.argv[2], ""))' "$DEF/scripts" "$1"; }

CFG_FIX="ONBOARDING.md → 3. Write it down"
if [ ! -f "$CONFIG" ]; then
  fail config "work/CONFIG.md is missing" "write it: $CFG_FIX"
else
  for k in $REQUIRED; do
    v="$(cfg "$k")"
    if [ -n "$v" ]; then ok "config.$k" "$v"; else fail "config.$k" "missing" "add \`- $k: <value>\`: $CFG_FIX"; fi
  done
  src="$(cfg source)"
  if [ -n "$src" ]; then
    if [ -f "$DEF/scripts/sources/$src.py" ]; then ok config.source "adapter scripts/sources/$src.py"
    else fail config.source "no adapter for '$src'" "use prometheus, clickhouse, command or demo: docs/sources.md"; fi
    case "$src" in
      prometheus|clickhouse)
        u="$(cfg source_url)"
        if [ -z "$u" ]; then fail config.source_url "missing for $src" "add \`- source_url: https://...\`: docs/sources.md"
        elif printf '%s' "$u" | grep -qE '^https?://[^/[:space:]]+'; then ok config.source_url "$u"
        else fail config.source_url "'$u' is not an http(s) URL" "docs/sources.md"; fi ;;
    esac
  fi
  # A credential in CONFIG.md is the one mistake that cannot be undone by editing it back.
  if grep -qiE '(authorization|api[-_]?key|password|secret|token|x-clickhouse-key)[[:space:]]*:' "$CONFIG"; then
    fail config.secrets "a credential-like header is in work/CONFIG.md" "remove it, rotate it, and add a Custom Header connection instead: docs/sources.md → Credentials"
  else
    ok config.secrets "no credential in CONFIG.md"
  fi
  vis="$(cfg visibility)"
  case "$vis" in private|public|restricted|'') ;; *) fail config.visibility "'$vis'" "one of private, public, restricted: $CFG_FIX" ;; esac
  for k in slack_channel report_to; do
    v="$(cfg "$k")"
    [ -z "$v" ] && { ok "config.$k" "none"; continue; }
    if printf '%s' "$v" | grep -qE '^[CGDUW][A-Z0-9]{6,}$'; then ok "config.$k" "$v"
    else fail "config.$k" "'$v' is not a Slack id" "use the id describe_channel / describe_channel_users gives, e.g. C0123ABCD or U0123ABCD: $CFG_FIX"; fi
  done
  unknown="$(grep -oE '^[-*][[:space:]]*[A-Za-z0-9_]+[[:space:]]*:' "$CONFIG" | sed -E 's/^[-*][[:space:]]*//; s/[[:space:]]*:$//' |
    tr '[:upper:]' '[:lower:]' | sort -u | while read -r k; do case " $KNOWN " in *" $k "*) ;; *) printf '%s ' "$k" ;; esac; done)"
  if [ -n "$unknown" ]; then fail config.keys "unknown: $unknown" "remove them, nothing reads them: $CFG_FIX"
  else ok config.keys "only known keys"; fi
fi

if [ -f "$WORK/metrics.json" ]; then
  if out="$(python3 "$DEF/scripts/fetch.py" --check-metrics 2>&1)"; then ok metrics "$out"
  else fail metrics "$out" "edit work/metrics.json: docs/metrics.md"; fi
else
  fail metrics "work/metrics.json is missing" "write it with the person, from examples/<source>/metrics.json: ONBOARDING.md → 2. Ask"
fi

if [ "$STRUCTURE" = 1 ]; then
  [ -f "$HOME/.metrics-monitor-onboarded" ] && ok sentinel "onboarded" ||
    fail sentinel "\$HOME/.metrics-monitor-onboarded is missing" "ONBOARDING.md → 5. Finish"
  [ -f "$WORK/VERSION" ] && ok version "adopted $(head -1 "$WORK/VERSION")" ||
    fail version "work/VERSION is missing" "head -1 \$HOME/VERSION > \$HOME/work/VERSION"
  [ -f "$WORK/AGENTS.md" ] && ok pointer "work/AGENTS.md" ||
    fail pointer "work/AGENTS.md is missing" "ONBOARDING.md → 2. Ask"
  [ -f "$WORK/logs/requirements-log.md" ] && ok requirements "work/logs/requirements-log.md" ||
    fail requirements "work/logs/requirements-log.md is missing" "ONBOARDING.md → 2. Ask"
  [ -d "$DEF/scripts/browser/node_modules/playwright-core" ] && ok browser "playwright-core installed" ||
    fail browser "scripts/browser/node_modules is missing" "cd \$HOME/scripts/browser && npm ci"
  if grep -qF 'publish_upload.sh' "$WORK/.claude/settings.json" 2>/dev/null; then ok allowlist "publish allow-list in work/.claude/settings.json"
  else fail allowlist "the publish allow-list is missing" "bash \$HOME/scripts/harness/claude-code/install.sh"; fi
fi

if [ "$LIVE" = 1 ]; then
  if out="$(python3 "$DEF/scripts/ask.py" list 2>&1)"; then ok ask "metrics listed"; else fail ask "$out" "docs/sources.md"; fi
  src="$(cfg source)"
  case "$src" in
    prometheus) probe='vector(1)' ;;
    clickhouse) probe='SELECT 1 AS value' ;;
    *) probe='' ;;
  esac
  if [ -n "$probe" ]; then
    if python3 "$DEF/scripts/ask.py" raw "$probe" >/dev/null 2>&1; then ok source "answers"
    else fail source "does not answer" "docs/sources.md → When the source does not answer"; fi
  fi
  last="$(tail -1 "$WORK/logs/refresh.log" 2>/dev/null)"
  case "$last" in
    *"  ok  "*|*"Z  ok "*) ok refresh "${last%%  *}: ok" ;;
    '') fail refresh "no refresh has run" "MM_NO_WAIT=1 bash \$HOME/scripts/refresh.sh: ONBOARDING.md → 4." ;;
    *) fail refresh "the last refresh failed" "docs/failures.md, then run it again" ;;
  esac
  aid="$(cfg artifact_id)"
  if [ -n "$aid" ]; then ok artifact "$aid"; else fail artifact "no artifact_id" "docs/publish.md → First publish"; fi
fi

echo
if [ "$FAILS" -eq 0 ]; then echo "PASS: $CHECKS checks, $WARNS warnings"; exit 0; fi
echo "FAIL: $FAILS of $CHECKS checks failed, $WARNS warnings"; exit 1
