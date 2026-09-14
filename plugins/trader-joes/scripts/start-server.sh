#!/bin/sh
set -eu

cd "${CLAUDE_PLUGIN_ROOT:-$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)}"

if command -v uv >/dev/null 2>&1; then
    exec uv run --no-dev python -m src.server
fi

exec python3 -m src.server
