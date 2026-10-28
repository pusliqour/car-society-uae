#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
SECRETS="$ROOT/.secrets/csae.env"
if [ ! -f "$SECRETS" ]; then
  echo "Missing $SECRETS. Copy .env.example and add the Telegram values." >&2
  exit 1
fi
MODE=$(stat -f '%Lp' "$SECRETS")
if [ "$MODE" != "600" ]; then
  echo "$SECRETS must have mode 600 (run: chmod 600 '$SECRETS')." >&2
  exit 1
fi
set -a
. "$SECRETS"
set +a
if [ -z "${GITHUB_TOKEN:-}" ] && command -v gh >/dev/null 2>&1; then
  GITHUB_TOKEN=$(gh auth token)
  export GITHUB_TOKEN
fi
exec "$ROOT/.venv/bin/python" -m csae.bot
