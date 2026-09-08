#!/usr/bin/env python3
"""Print per-trial rewards and the calls behind process failures."""

import json
import sys
from pathlib import Path

MCP_PREFIX = "mcp__target__"
ARG_WIDTH = 160


def _rewards(trial: Path) -> dict[str, float]:
    for path in sorted(trial.rglob("reward.json")):
        try:
            data = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        found = {key: float(value) for key, value in data.items() if isinstance(value, int | float)}
        if found:
            return found

    found = {}
    for path in sorted(trial.rglob("test-stdout.txt")):
        try:
            lines = path.read_text().splitlines()
        except OSError:
            continue
        for line in lines:
            name, _, value = line.partition(":")
            try:
                found[name.strip()] = float(value)
            except ValueError:
                continue
    return found


def _calls(trial: Path) -> list[tuple[str, str]]:
    for path in sorted(trial.rglob("trajectory.json")):
        try:
            data = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        return [
            (str(call.get("function_name") or "?"), json.dumps(call.get("arguments") or {}))
            for step in data.get("steps") or []
            for call in step.get("tool_calls") or []
        ]
    return []


def explain(job_dir: Path) -> None:
    trials = sorted(path for path in job_dir.iterdir() if path.is_dir())
    if not trials:
        print(f"no trial directories under {job_dir}")
        return

    for trial in trials:
        rewards = _rewards(trial)
        if not rewards:
            continue
        summary = ", ".join(f"{name}={value}" for name, value in sorted(rewards.items()))
        print(f"\n== {trial.name}: {summary}")
        if rewards.get("process", 0.0) >= 1.0:
            continue

        calls = _calls(trial)
        if not calls:
            print("   no trajectory recorded, so process fails closed at 0")
            continue
        mcp = sum(1 for name, _ in calls if name.startswith(MCP_PREFIX))
        print(f"   {len(calls)} tool call(s), {mcp} through the MCP server:")
        for name, arguments in calls:
            marker = "  " if name.startswith(MCP_PREFIX) else "! "
            print(f"   {marker}{name} {arguments[:ARG_WIDTH]}")


if __name__ == "__main__":
    explain(Path(sys.argv[1]))
