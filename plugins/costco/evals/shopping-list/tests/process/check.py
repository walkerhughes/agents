"""Verify that the answer came through the Costco MCP server."""

import json
import re
from pathlib import Path

from rewardkit import criterion

TRAJECTORY = Path("/logs/agent/trajectory.json")
SESSIONS = Path("/logs/agent/sessions")
EXPECTED_TOOLS = json.loads(r"""["mcp__costco__price_shopping_list"]""")
BYPASS = re.compile(r":8091\b|mock_server\.py|/opt/eval", re.IGNORECASE)


def _calls():
    calls = []
    try:
        data = json.loads(TRAJECTORY.read_text())
        calls.extend(call for step in data.get("steps") or [] for call in step.get("tool_calls") or [])
    except (OSError, json.JSONDecodeError):
        pass
    for path in sorted(SESSIONS.rglob("*.jsonl")):
        try:
            lines = path.read_text().splitlines()
        except OSError:
            continue
        for line in lines:
            try:
                blocks = (json.loads(line).get("message") or {}).get("content")
            except json.JSONDecodeError:
                continue
            if not isinstance(blocks, list):
                continue
            for block in blocks:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    calls.append({"function_name": block.get("name"), "arguments": block.get("input")})
    return calls


@criterion(description="Agent called every expected Costco MCP tool")
def used_mcp_tool(workspace: Path) -> bool:
    called = {str(call.get("function_name") or "") for call in _calls()}
    return all(tool in called for tool in EXPECTED_TOOLS)


@criterion(description="Agent did not bypass the Costco MCP server")
def no_direct_endpoint_access(workspace: Path) -> bool:
    calls = _calls()
    if not calls:
        return False
    for call in calls:
        if str(call.get("function_name") or "").startswith("mcp__costco__"):
            continue
        if BYPASS.search(json.dumps(call.get("arguments") or {})):
            return False
    return True
