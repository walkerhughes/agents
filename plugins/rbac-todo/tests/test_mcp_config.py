"""Keep both clients authenticated when updating plugin configuration."""

import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / ".codex-plugin/plugin.json").read_text())
codex = json.loads((root / manifest["mcpServers"]).read_text())["mcpServers"]["rbac-todo"]
claude = json.loads((root / ".mcp.json").read_text())["mcpServers"]["rbac-todo"]
assert codex["url"] == claude["url"]
assert codex["bearer_token_env_var"] == "RBAC_TODO_ACCESS_TOKEN"
assert claude["headers"]["Authorization"] == "Bearer ${RBAC_TODO_ACCESS_TOKEN}"
print("PASS: both clients use the user token and the same MCP endpoint")
