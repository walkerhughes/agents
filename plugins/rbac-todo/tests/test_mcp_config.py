"""Keep both clients authenticated when updating plugin configuration."""

import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / ".codex-plugin/plugin.json").read_text())
codex = json.loads((root / manifest["mcpServers"]).read_text())["mcpServers"]["rbac-todo"]
claude = json.loads((root / ".mcp.json").read_text())["mcpServers"]["rbac-todo"]
assert codex["url"] == claude["url"]
assert set(codex) == {"url"}, "Codex must discover OAuth without a static token"
assert set(claude) == {"url", "type"}, "Claude must discover OAuth without static headers"
print("PASS: both clients use OAuth discovery and the same MCP endpoint")
