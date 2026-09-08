"""Safeway MCP server."""

import json
from pathlib import Path

from mcp.server import MCPServer

from .tools import register_all

_MANIFEST = Path(__file__).resolve().parent.parent / ".claude-plugin" / "plugin.json"

INSTRUCTIONS = (
    "Read-only access to Safeway's public store resolver and store-scoped product "
    "search. Start with find_stores when store context is unknown. Preserve store and "
    "fulfillment channel for every price. Treat current price, base price, promotions, "
    "and inventory as distinct signals; never promise loyalty eligibility or shelf stock."
)


def version() -> str:
    try:
        return str(json.loads(_MANIFEST.read_text())["version"])
    except (OSError, ValueError, KeyError):
        return ""


def build_server() -> MCPServer:
    server = MCPServer("safeway", instructions=INSTRUCTIONS, version=version())
    register_all(server)
    return server


mcp = build_server()


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
