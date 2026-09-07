#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HARBOR_TEST_ENV="${HARBOR_TEST_ENV:-docker}"
HARBOR_MCP_REF="${HARBOR_MCP_REF:-main}"
JOB_NAME="ci-evals-trader-joes"

[ -n "${CLAUDE_CODE_OAUTH_TOKEN:-}" ] \
    || { echo "error: CLAUDE_CODE_OAUTH_TOKEN is not set" >&2; exit 1; }
[ -z "${EVALS_UPLOAD:-}" ] || [ -n "${HARBOR_API_KEY:-}" ] \
    || { echo "error: EVALS_UPLOAD needs HARBOR_API_KEY" >&2; exit 1; }

OUT="${EVALS_OUT_DIR:-}"
if [ -n "$OUT" ]; then
    mkdir -p "$OUT"
    KEEP=1
else
    OUT="$(mktemp -d)"
    KEEP=0
fi
trap '[ "$KEEP" -eq 1 ] || rm -rf "$OUT"' EXIT

EVALS_SRC="$OUT/evals-src"
cp -R "$ROOT/evals" "$EVALS_SRC"
while IFS= read -r dockerfile; do
    sed -i.bak "s|git -C /opt/claude checkout main|git -C /opt/claude checkout ${HARBOR_MCP_REF}|" "$dockerfile"
    rm -f "$dockerfile.bak"
done < <(find "$EVALS_SRC" -name Dockerfile -type f)

args=(-y -p "$EVALS_SRC" -a claude-code -e "$HARBOR_TEST_ENV" -o "$OUT" --job-name "$JOB_NAME")
if [ -n "${EVALS_UPLOAD:-}" ]; then
    args+=(--upload)
fi

harbor run "${args[@]}"
if ! python3 "$ROOT/evals/check_reward.py" "$OUT/$JOB_NAME/result.json" "$JOB_NAME"; then
    echo "--- trials ---" >&2
    python3 "$ROOT/evals/explain_trials.py" "$OUT/$JOB_NAME" >&2 || true
    exit 1
fi
