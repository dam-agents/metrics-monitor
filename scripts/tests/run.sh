#!/usr/bin/env bash
# Offline test suite: no network, no credentials. Builds a demo instance in a
# temporary MM_WORK, runs the whole refresh on it (the browser check too when
# a browser and scripts/browser/node_modules are there), then the unit tests
# and the definition's config-key parity.
set -u
DEF="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$DEF" || exit 1
export MM_WORK="$(mktemp -d)"; trap 'rm -rf "$MM_WORK"' EXIT
export MM_NO_WAIT=1
FAILS=0
t() { if "$@"; then echo "PASS  $name"; else echo "FAIL  $name"; FAILS=$((FAILS + 1)); fi; }

cp examples/demo/metrics.json "$MM_WORK/"
printf -- '- source: demo\n- title: Test\n- visibility: private\n' > "$MM_WORK/CONFIG.md"

[ -d scripts/browser/node_modules/playwright-core ] || { echo "no scripts/browser/node_modules: browser check skipped"; export MM_NO_BROWSER=1; }
name="refresh.sh on the demo source (first pull)"
t bash -c 'bash scripts/refresh.sh > "$MM_WORK/out1" 2>&1 || { tail -30 "$MM_WORK/out1"; false; }'
name="refresh.sh again (incremental, compared with the previous snapshot)"
t bash -c 'bash scripts/refresh.sh > "$MM_WORK/out2" 2>&1 && grep -q "total up to the previous end kept" "$MM_WORK/out2" || { tail -30 "$MM_WORK/out2"; false; }'
name="refresh.log has one line per run"
t bash -c '[ "$(grep -c "  ok  " "$MM_WORK/logs/refresh.log")" = 2 ]'

name="a changed query re-pulls its metric and skips its comparison once"
t bash -c 'python3 - <<PY
import json, os
p = os.environ["MM_WORK"] + "/metrics.json"; s = json.load(open(p))
s["metrics"][3]["query"] = "errors "; json.dump(s, open(p, "w"))
PY
bash scripts/refresh.sh > "$MM_WORK/out3" 2>&1 && grep -q "errors: new metric or changed query: full history" "$MM_WORK/out3" \
  && grep -q "WARN  errors: new metric or changed query" "$MM_WORK/out3" || { tail -30 "$MM_WORK/out3"; false; }'

name="a failed refresh restores the previous snapshot"
t bash -c 'before="$(sha256sum < "$MM_WORK/data/snapshot.json")"
printf -- "- source: nosuch\n- title: Test\n- visibility: private\n" > "$MM_WORK/CONFIG.md"
! bash scripts/refresh.sh > "$MM_WORK/out4" 2>&1 &&
printf -- "- source: demo\n- title: Test\n- visibility: private\n" > "$MM_WORK/CONFIG.md" &&
[ "$(sha256sum < "$MM_WORK/data/snapshot.json")" = "$before" ] && tail -1 "$MM_WORK/logs/refresh.log" | grep -q "FAILED at fetch"'

name="unit tests"
t python3 scripts/tests/test_pipeline.py

name="ask.py answers live with unit and UTC window"
t bash -c 'out="$(python3 scripts/ask.py requests --since 24h)" && echo "$out" | grep -qE "^Requests served: [0-9.]+[KMB]? requests$" && echo "$out" | grep -qE "^window: .* UTC .* UTC \(24 h\)"'

# Every CONFIG.md key is named in CLAUDE.md, accepted by the verifier, and
# the ONBOARDING example uses only known keys.
name="config keys agree across CLAUDE.md, verify-onboarding.sh and ONBOARDING.md"
t bash -c '
known="$(sed -n "s/^KNOWN=\"\(.*\)\"$/\1/p" scripts/verify-onboarding.sh)"
claude="$(python3 scripts/tests/config_keys.py CLAUDE.md)"
example="$(sed -n "/^## 3. Write it down/,/^## /p" ONBOARDING.md | grep -oE "^- [a-z_]+:" | grep -oE "[a-z_]+" | sort -u)"
rc=0
for k in $known; do echo "$claude" | grep -qx "$k" || { echo "  $k is in KNOWN but not in CLAUDE.md"; rc=1; }; done
for k in $claude; do case " $known " in *" $k "*) ;; *) echo "  $k is in CLAUDE.md but not in KNOWN"; rc=1 ;; esac; done
for k in $example; do case " $known " in *" $k "*) ;; *) echo "  $k is in the ONBOARDING example but not in KNOWN"; rc=1 ;; esac; done
exit $rc'

name="verify-onboarding.sh --config passes on the demo instance"
t bash -c 'bash scripts/verify-onboarding.sh --config > "$MM_WORK/vo" || { cat "$MM_WORK/vo"; false; }'
name="verify-onboarding.sh refuses a credential in CONFIG.md"
t bash -c 'cp "$MM_WORK/CONFIG.md" "$MM_WORK/c.bak"; echo "- source_headers: Authorization: Bearer x" >> "$MM_WORK/CONFIG.md"
out="$(bash scripts/verify-onboarding.sh --config)"; rc=$?; mv "$MM_WORK/c.bak" "$MM_WORK/CONFIG.md"
[ $rc -ne 0 ] && echo "$out" | grep -q "FAIL config.secrets"'

echo
[ "$FAILS" -eq 0 ] && { echo "all tests passed"; exit 0; }
echo "$FAILS test(s) failed"; exit 1
