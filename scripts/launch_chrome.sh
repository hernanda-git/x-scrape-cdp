#!/usr/bin/env bash
set -euo pipefail

PORT="${1:-9222}"
USER_DATA_DIR="${2:-./data/chrome_profile}"

mkdir -p "$USER_DATA_DIR"

if command -v google-chrome >/dev/null 2>&1; then
  CHROME_BIN="google-chrome"
elif command -v chromium >/dev/null 2>&1; then
  CHROME_BIN="chromium"
elif command -v "Google Chrome" >/dev/null 2>&1; then
  CHROME_BIN="Google Chrome"
else
  echo "Chrome/Chromium not found in PATH." >&2
  exit 1
fi

"$CHROME_BIN" \
  --remote-debugging-port="$PORT" \
  --user-data-dir="$USER_DATA_DIR" \
  --no-first-run \
  --no-default-browser-check >/dev/null 2>&1 &

echo "Chrome launched with CDP at http://127.0.0.1:$PORT"
echo "Check endpoint: http://127.0.0.1:$PORT/json/version"
