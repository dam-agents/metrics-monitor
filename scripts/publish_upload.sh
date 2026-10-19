#!/usr/bin/env bash
# PUT the built dashboard to a presigned URL from the platform's create_artifact_upload_url.
#
#   bash scripts/publish_upload.sh '<url>' [file]     (file defaults to work/dist/dashboard.html)
#
# Run it as a command of its own (no cd, && or pipes), so the allow-list entry in
# .claude/settings.json matches and an unattended run needs no approval. Raw curl uploads have
# been refused by the auto-mode permission check; this script is the one sanctioned path.
# The Content-Type matters: without it the artifact store keeps the page form-urlencoded.
set -euo pipefail
WORK="${MM_WORK:-$HOME/work}"
url="${1:?upload url from create_artifact_upload_url}"
file="${2:-$WORK/dist/dashboard.html}"
case "$url" in
  http://*/platform-artifacts/*|https://*/platform-artifacts/*) ;;
  *) echo "refused: not the platform artifact store: ${url%%\?*}" >&2; exit 2 ;;
esac
real="$(realpath "$file")"
case "$real" in "$(realpath "$WORK")"/dist/*.html) ;; *) echo "refused: $file is not a work/dist/*.html build" >&2; exit 2 ;; esac
for i in 1 2 3; do
  code=$(curl -sS -o /dev/null -w '%{http_code}' -H 'Content-Type: text/html; charset=utf-8' -T "$real" "$url" || echo 000)
  [ "$code" = 200 ] && { echo "uploaded $file ($(stat -c %s "$real") bytes) http 200"; exit 0; }
  echo "attempt $i: http $code" >&2; sleep 5
done
exit 1
