#!/usr/bin/env python3
"""Generate the Trader Joe's Harbor tasks from one compact specification."""

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent

TASKS = {
    "nearest-store": {
        "description": "Find the nearest Trader Joe's to ZIP code 94109.",
        "instruction": (
            "Find the nearest Trader Joe's to ZIP code 94109. Report its numeric store code and full store name."
        ),
        "tool": "find_stores",
        "answer": {"store_code": "200", "name": "San Francisco - Nob Hill (200)"},
    },
    "coffee-price": {
        "description": "Find the published price of Costa Rica Coffee at store 200.",
        "instruction": (
            "At Trader Joe's store 200, find Costa Rica Coffee and report its product name "
            "and published price as a number."
        ),
        "tool": "search_products",
        "answer": {"name": "Costa Rica Coffee", "price": 9.99},
    },
    "product-by-sku": {
        "description": "Look up a known Trader Joe's product by SKU at store 200.",
        "instruction": (
            "At Trader Joe's store 200, look up SKU 081522 and report its product name, "
            "package size, and published price as a number."
        ),
        "tool": "get_product",
        "answer": {"name": "Costa Rica Coffee", "size": "12 Oz", "price": 9.99},
    },
    "shopping-list": {
        "description": "Price a two-item shopping list at Trader Joe's store 200.",
        "instruction": (
            "At Trader Joe's store 200, price a list containing one package of Costa Rica "
            "Coffee and one package of Oat Beverage. Report the selected product names and "
            "the combined estimated total as a number."
        ),
        "tool": "price_shopping_list",
        "answer": {
            "items": ["Costa Rica Coffee", "Non-Dairy Oat Beverage"],
            "estimated_total": 12.48,
        },
    },
}

TASK_TOML = """schema_version = "1.1"

[task]
name = "trader-joes/{name}"
description = {description}
authors = []
keywords = ["mcp", "trader-joes", "eval"]

[metadata]
category = "mcp"
difficulty = "easy"

[agent]
timeout_sec = 300.0

[verifier]
timeout_sec = 60.0

[environment]
build_timeout_sec = 900.0
cpus = 1
memory_mb = 2048
storage_mb = 10240
gpus = 0
network_mode = "public"

[[environment.mcp_servers]]
name = "trader-joes"
transport = "stdio"
command = "/opt/eval/start-mcp"
args = []
"""

INSTRUCTION = """# Task

{instruction}

Use the Trader Joe's integration tools available in this environment. All store and
product data must come through those tools, not shell commands, local files, direct
web requests, or Python imports. If a tool reports an error, use its guidance and try
the integration again rather than working around it.

Write the answer to `/app/answer.json` as one JSON object with exactly this shape:

```json
{shape}
```
"""

DOCKERFILE = """FROM python:3.13-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \\
    ca-certificates curl git \\
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN git clone https://github.com/walkerhughes/claude.git /opt/claude \\
    && git -C /opt/claude checkout main \\
    && cd /opt/claude/plugins/trader-joes \\
    && uv sync --frozen --no-dev

RUN python -m venv /opt/rewardkit \\
    && /opt/rewardkit/bin/pip install --no-cache-dir "harbor-rewardkit==0.1.*" \\
    && ln -s /opt/rewardkit/bin/rewardkit /usr/local/bin/rewardkit

COPY mock_server.py start-mcp /opt/eval/
RUN chmod +x /opt/eval/start-mcp

WORKDIR /app
ENV TRADER_JOES_PRODUCT_URL=http://127.0.0.1:8091/graphql \\
    TRADER_JOES_LOCATOR_URL=http://127.0.0.1:8091/locator
"""

START_MCP = """#!/bin/sh
set -eu

python /opt/eval/mock_server.py >/tmp/trader-joes-mock.log 2>&1 &
mock_pid=$!
trap 'kill "$mock_pid" 2>/dev/null || true' EXIT INT TERM

for attempt in $(seq 1 50); do
    if curl -sf http://127.0.0.1:8091/health >/dev/null; then
        cd /opt/claude/plugins/trader-joes
        exec uv run --no-dev python -m src.server
    fi
    sleep 0.1
done

cat /tmp/trader-joes-mock.log >&2
exit 1
"""

MOCK_SERVER = r'''#!/usr/bin/env python3
"""Deterministic local stand-in for the two public website endpoints."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

COFFEE = {
    "sku": "081522",
    "item_title": "Costa Rica Coffee",
    "retail_price": "9.99",
    "sales_size": 12,
    "sales_uom_description": "Oz",
    "availability": "1",
    "url_key": "costa-rica-coffee-081522",
    "category_hierarchy": [{"id": 194, "name": "Coffee & Tea"}],
}
OAT = {
    "sku": "099001",
    "item_title": "Non-Dairy Oat Beverage",
    "retail_price": "2.49",
    "sales_size": 32,
    "sales_uom_description": "Fl Oz",
    "availability": "1",
    "url_key": "non-dairy-oat-beverage-099001",
    "category_hierarchy": [{"id": 183, "name": "Non-Dairy Beverages"}],
}
STORE = {
    "clientkey": "200",
    "name": "San Francisco - Nob Hill (200)",
    "address1": "1095 Hyde St",
    "city": "San Francisco",
    "state": "CA",
    "postalcode": "94109",
    "_distance": "0.24",
    "phone": "415-292-7665",
    "website": "https://locations.traderjoes.com/ca/san-francisco/200/",
}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_GET(self):
        if self.path == "/health":
            self._send({"ok": True})
            return
        self.send_error(404)

    def do_POST(self):
        size = int(self.headers.get("Content-Length", "0"))
        request = json.loads(self.rfile.read(size) or b"{}")
        if self.path == "/locator":
            self._send({"code": 1, "response": {"collection": [STORE]}})
            return
        if self.path == "/graphql":
            variables = request.get("variables") or {}
            search = str(variables.get("search") or "").lower()
            sku = str(variables.get("sku") or "")
            if sku:
                items = [COFFEE] if sku == COFFEE["sku"] else []
            elif "oat" in search:
                items = [OAT]
            elif "coffee" in search:
                items = [COFFEE]
            else:
                items = []
            self._send(
                {
                    "data": {
                        "products": {
                            "items": items,
                            "total_count": len(items),
                            "page_info": {
                                "current_page": 1,
                                "page_size": len(items),
                                "total_pages": 1,
                            },
                        }
                    }
                }
            )
            return
        self.send_error(404)

    def _send(self, payload):
        body = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


ThreadingHTTPServer(("127.0.0.1", 8091), Handler).serve_forever()
'''

PROCESS_CHECK = '''"""Verify that the answer came through the Trader Joe's MCP server."""

import json
import re
from pathlib import Path

from rewardkit import criterion

TRAJECTORY = Path("/logs/agent/trajectory.json")
SESSIONS = Path("/logs/agent/sessions")
EXPECTED_TOOL = "mcp__trader-joes__{tool}"
BYPASS = re.compile(r":8091\\b|mock_server\\.py|/opt/eval", re.IGNORECASE)


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
                blocks = (json.loads(line).get("message") or {{}}).get("content")
            except json.JSONDecodeError:
                continue
            if not isinstance(blocks, list):
                continue
            for block in blocks:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    calls.append({{"function_name": block.get("name"), "arguments": block.get("input")}})
    return calls


@criterion(description="Agent called the expected Trader Joe's MCP tool")
def used_mcp_tool(workspace: Path) -> bool:
    return any(str(call.get("function_name") or "") == EXPECTED_TOOL for call in _calls())


@criterion(description="Agent did not bypass the Trader Joe's MCP server")
def no_direct_endpoint_access(workspace: Path) -> bool:
    calls = _calls()
    if not calls:
        return False
    for call in calls:
        if str(call.get("function_name") or "").startswith("mcp__trader-joes__"):
            continue
        if BYPASS.search(json.dumps(call.get("arguments") or {{}})):
            return False
    return True
'''

OUTCOME_CHECK = '''"""Compare the submitted answer with deterministic fixture truth."""

import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

from rewardkit import criterion

EXPECTED = json.loads(
    r"""{expected}"""
)


def _matches(actual, expected):
    if isinstance(expected, float):
        try:
            return Decimal(str(actual)) == Decimal(str(expected))
        except (InvalidOperation, TypeError, ValueError):
            return False
    if isinstance(expected, list):
        if isinstance(actual, str) and all(isinstance(item, str) for item in expected):
            actual = [item.strip() for item in actual.split(",")]
        return (
            isinstance(actual, list)
            and len(actual) == len(expected)
            and all(
                _matches(actual_item, expected_item)
                for actual_item, expected_item in zip(actual, expected, strict=True)
            )
        )
    if isinstance(expected, dict):
        return (
            isinstance(actual, dict)
            and actual.keys() == expected.keys()
            and all(_matches(actual[key], value) for key, value in expected.items())
        )
    return actual == expected


@criterion(description="Answer matches the mock catalog and store data")
def answer_matches(workspace: Path) -> bool:
    try:
        answer = json.loads((workspace / "answer.json").read_text())
    except (OSError, json.JSONDecodeError):
        return False
    return _matches(answer, EXPECTED)
'''


def answer_shape(answer: dict) -> dict:
    shape = {}
    for key, value in answer.items():
        if isinstance(value, list):
            shape[key] = ["<item 1>", "<item 2>"]
        elif isinstance(value, float):
            shape[key] = 0.0
        else:
            shape[key] = f"<{key}>"
    return shape


def main() -> None:
    for child in ROOT.iterdir():
        if child.is_dir() and child.name in TASKS:
            shutil.rmtree(child)

    for name, spec in TASKS.items():
        task = ROOT / name
        (task / "environment").mkdir(parents=True)
        (task / "solution").mkdir()
        (task / "tests" / "outcome").mkdir(parents=True)
        (task / "tests" / "process").mkdir()

        (task / "task.toml").write_text(TASK_TOML.format(name=name, description=json.dumps(spec["description"])))
        (task / "instruction.md").write_text(
            INSTRUCTION.format(
                instruction=spec["instruction"],
                shape=json.dumps(answer_shape(spec["answer"]), indent=2),
            )
        )
        (task / "environment" / "Dockerfile").write_text(DOCKERFILE)
        (task / "environment" / "mock_server.py").write_text(MOCK_SERVER)
        (task / "environment" / "start-mcp").write_text(START_MCP)
        (task / "solution" / "solve.sh").write_text(
            "#!/bin/sh\nset -eu\ncat > /app/answer.json <<'EOF'\n" + json.dumps(spec["answer"]) + "\nEOF\n"
        )
        (task / "tests" / "test.sh").write_text("#!/bin/sh\nset -eu\nrewardkit /tests\n")
        (task / "tests" / "outcome" / "check.py").write_text(
            OUTCOME_CHECK.format(expected=json.dumps(spec["answer"], indent=2))
        )
        (task / "tests" / "process" / "check.py").write_text(PROCESS_CHECK.format(tool=spec["tool"]))
        for executable in (
            task / "environment" / "start-mcp",
            task / "solution" / "solve.sh",
            task / "tests" / "test.sh",
        ):
            executable.chmod(0o755)


if __name__ == "__main__":
    main()
