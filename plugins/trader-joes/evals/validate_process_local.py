#!/usr/bin/env python3
"""Exercise every real process checker against synthetic routes and bypasses."""

import importlib.util
import json
import sys
import tempfile
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _stub_rewardkit() -> None:
    def criterion(*args, **kwargs):
        if args and callable(args[0]):
            return args[0]
        return lambda function: function

    module = types.ModuleType("rewardkit")
    module.criterion = criterion
    sys.modules["rewardkit"] = module


def _load(path: Path):
    spec = importlib.util.spec_from_file_location(f"check_{path.parents[2].name}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _call(name: str, **arguments) -> dict:
    return {"function_name": name, "arguments": arguments}


def _trajectory(*calls: dict) -> dict:
    return {"steps": [{"tool_calls": list(calls)}]}


def _session(name: str, **arguments) -> str:
    return json.dumps({"message": {"content": [{"type": "tool_use", "name": name, "input": arguments}]}})


def _score(module, trajectory: dict | None, session_lines: list[str]) -> tuple[bool, bool]:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        module.TRAJECTORY = root / "trajectory.json"
        module.SESSIONS = root / "sessions"
        if trajectory is not None:
            module.TRAJECTORY.write_text(json.dumps(trajectory))
        if session_lines:
            target = module.SESSIONS / "subagents"
            target.mkdir(parents=True)
            (target / "delegate.jsonl").write_text("\n".join(session_lines))
        return module.used_mcp_tool(root), module.no_direct_endpoint_access(root)


def main() -> int:
    _stub_rewardkit()
    failures = []
    checkers = sorted(ROOT.glob("*/tests/process/check.py"))
    for path in checkers:
        module = _load(path)
        tool = module.EXPECTED_TOOL
        agent = _trajectory(_call("Agent", prompt="delegate"))
        cases = [
            ("solved", _trajectory(_call(tool)), [], (True, True)),
            ("empty", None, [], (False, False)),
            ("bypassed", _trajectory(_call("Bash", command="curl http://127.0.0.1:8091")), [], (False, False)),
            (
                "fallback",
                _trajectory(_call(tool), _call("Bash", command="curl http://localhost:8091")),
                [],
                (True, False),
            ),
            ("delegated", agent, [_session(tool)], (True, True)),
            ("delegated-bypass", agent, [_session("Bash", command="python /opt/eval/mock_server.py")], (False, False)),
            ("benign-shell", _trajectory(_call(tool), _call("Bash", command="pwd")), [], (True, True)),
        ]
        for name, trajectory, sessions, expected in cases:
            actual = _score(module, trajectory, sessions)
            if actual != expected:
                failures.append(f"{path.parents[2].name}/{name}: expected {expected}, got {actual}")
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(f"process criteria ok: {len(checkers) * 7} checks across {len(checkers)} evals")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
