#!/bin/sh
set -eu

PLUGIN_ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$PLUGIN_ROOT"

if command -v uv >/dev/null 2>&1; then
    exec uv run --no-dev python -m src.server
fi

exec python3 -m src.server
