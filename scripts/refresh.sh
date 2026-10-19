#!/usr/bin/env bash
# refresh.sh: fetch -> freshness check -> build -> cross-check -> browser check. Publishing is a
# separate step with the platform's artifact tools (docs/publish.md), so a bad pull is never published.
#
#   bash scripts/refresh.sh
#
# Exit 0: work/dist/dashboard.html is ready to publish. Non-zero: the step that failed is in the
# last line of work/logs/refresh.log, and the previous snapshot is put back (and rebuilt), so
# work/ matches what is live. Every run appends one line to work/logs/refresh.log and keeps its
# full output in work/logs/runs/<UTC time>.txt.
set -euo pipefail
DEF="$(cd "$(dirname "$0")/.." && pwd)"
WORK="${MM_WORK:-$HOME/work}"
export MM_WORK="$WORK"
mkdir -p "$WORK/logs/runs" "$WORK/data" "$WORK/dist"
RUN="$WORK/logs/runs/$(date -u +%Y-%m-%dT%H%M%SZ).txt"; T0=$(date +%s); step=fetch
SNAP="$WORK/data/snapshot.json"; PREV="$WORK/data/snapshot.prev.json"
TMP="$(mktemp -d)"
exec > >(tee "$RUN") 2>&1

finish() {
  rc=$?; set +e
  restored=""
  if [ $rc -ne 0 ] && [ -f "$PREV" ]; then
    cp "$PREV" "$SNAP" && python3 "$DEF/scripts/build.py" > /dev/null && restored="  previous snapshot restored"
  fi
  cnt() { [ -f "$2" ] && { grep -cE "$1" "$2" || true; } || echo 0; }
  end=$(python3 -c "import json,time,sys;print(time.strftime('%Y-%m-%d %H:%M UTC',time.gmtime(json.load(open(sys.argv[1]))['meta']['end'])))" "$SNAP" 2>/dev/null || echo '?')
  status=$([ $rc -eq 0 ] && echo "ok" || echo "FAILED at $step (exit $rc)")
  printf '%s  %-26s  %4ss  data to %s  verify %s ok %s fail  snapshot %s ok %s warn %s fail  %s%s\n' \
    "$(date -u +%FT%TZ)" "$status" "$(( $(date +%s) - T0 ))" "$end" \
    "$(cnt '^ok' "$TMP/verify")" "$(cnt '^FAIL' "$TMP/verify")" \
    "$(cnt '^ok' "$TMP/snapshot")" "$(cnt '^WARN' "$TMP/snapshot")" "$(cnt '^FAIL' "$TMP/snapshot")" \
    "${RUN#"$WORK"/}" "$restored" >> "$WORK/logs/refresh.log"
  rm -rf "$TMP"
}
trap finish EXIT

# A schedule can fire a minute or two early; the fetch would then end a bucket short and the page
# would stay an hour behind. Started after :55, wait until just past the hour.
if [ -z "${MM_NO_WAIT:-}" ]; then
  s=$(( $(date -u +%s) % 3600 )); if [ "$s" -ge 3300 ]; then sleep $(( 3600 - s + 30 )); fi
fi

[ -f "$SNAP" ] && cp "$SNAP" "$PREV"
python3 "$DEF/scripts/fetch.py" --out "$SNAP"

step=freshness
python3 "$DEF/scripts/check_snapshot.py" "$SNAP" "$PREV" > "$TMP/snapshot" || { cat "$TMP/snapshot"; echo "freshness/completeness check failed"; exit 4; }
cat "$TMP/snapshot"

step=build
python3 "$DEF/scripts/build.py"

step=verify
python3 "$DEF/scripts/verify.py" --check --hours "${MM_VERIFY_HOURS:-168}" > "$TMP/verify" || { cat "$TMP/verify"; echo "cross-check failed"; exit 2; }
cat "$TMP/verify"

step=browser
if [ -n "${MM_NO_BROWSER:-}" ]; then
  echo "browser check skipped (MM_NO_BROWSER)"
else
  out=""
  for try in 1 2; do   # the headless browser crashes now and then: one retry
    out="$(node "$DEF/scripts/browser/check.mjs" "$WORK/dist/dashboard.html" 2>&1 | tail -20)" || true
    [ "$out" = "done" ] && break
  done
  [ "$out" = "done" ] || { echo "$out"; echo "browser check failed"; exit 3; }
  echo "browser check: every range renders with no errors"
fi
echo "refresh ok: work/dist/dashboard.html ready to publish"
