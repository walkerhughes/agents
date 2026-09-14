#!/usr/bin/env python3
"""Fail unless every completed Harbor trial earned every reward."""

import json
import sys
from pathlib import Path


def rewards(stats: dict) -> tuple[list[float] | None, str]:
    if stats.get("n_errored_trials") or not stats.get("n_completed_trials"):
        return None, f"run did not complete cleanly (stats={stats})"
    found = [
        value
        for eval_stats in stats.get("evals", {}).values()
        for metric in eval_stats.get("metrics", [])
        for value in metric.values()
    ]
    if not found:
        return None, "no rewards reported"
    return found, ""


def gate(stats: dict) -> tuple[bool, str]:
    found, reason = rewards(stats)
    if found is None:
        return False, reason
    if any(reward != 1 for reward in found):
        mean = sum(found) / len(found)
        return False, f"reward not perfect (mean={mean:.3f}, rewards={found})"
    return True, f"reward 1.0 over {stats['n_completed_trials']} trial(s)"


def _selftest() -> None:
    ok = {
        "n_completed_trials": 2,
        "evals": {"task": {"metrics": [{"outcome": 1.0, "process": 1.0}]}},
    }
    assert gate(ok)[0]
    split = {**ok, "evals": {"task": {"metrics": [{"outcome": 1.0, "process": 0.0}]}}}
    assert not gate(split)[0]
    assert not gate({**ok, "n_errored_trials": 1})[0]
    assert not gate({"n_completed_trials": 0, "evals": {}})[0]
    assert not gate({"n_completed_trials": 1, "evals": {}})[0]
    print("check_reward selftest ok")


def main(argv: list[str]) -> int:
    if argv[1:2] == ["--selftest"]:
        _selftest()
        return 0
    if len(argv) != 3:
        print("usage: check_reward.py RESULT_JSON NAME", file=sys.stderr)
        return 2
    result_path, name = argv[1], argv[2]
    try:
        stats = json.loads(Path(result_path).read_text()).get("stats", {})
    except (OSError, json.JSONDecodeError) as exc:
        print(f"{name}: could not read result: {exc}", file=sys.stderr)
        return 1
    ok, message = gate(stats)
    print(f"{name}: {message}", file=sys.stdout if ok else sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
