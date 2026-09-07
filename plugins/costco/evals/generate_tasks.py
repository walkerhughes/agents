#!/usr/bin/env python3
"""Generate the Costco Harbor tasks from one compact specification."""

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent

TASKS = {
    "nearest-warehouse": {
        "description": "Find the nearest Costco warehouse to ZIP code 94109.",
        "instruction": (
            "Find the nearest Costco warehouse to ZIP code 94109. Report its numeric "
            "warehouse number and full warehouse name."
        ),
        "tool": "find_warehouses",
        "answer": {"warehouse_number": "144", "name": "South San Francisco"},
    },
    "quinoa-price": {
        "description": "Find the public price of organic quinoa for warehouse 144.",
        "instruction": (
            "For Costco warehouse 144 and postal code 94080, find organic quinoa and "
            "report the selected product name and public Costco.com price as a number."
        ),
        "tool": "search_products",
        "answer": {"name": "Kirkland Signature Organic Quinoa, 4.5 lb", "price": 18.99},
    },
    "product-by-item": {
        "description": "Look up a Costco product by item number for warehouse 144.",
        "instruction": (
            "For Costco warehouse 144, look up item number 1234567 and report its "
            "product name and public Costco.com price as a number."
        ),
        "tool": "get_product",
        "answer": {"name": "Kirkland Signature Organic Quinoa, 4.5 lb", "price": 18.99},
    },
    "shopping-list": {
        "description": "Price a two-item shopping list for Costco warehouse 144.",
        "instruction": (
            "For Costco warehouse 144 and postal code 94080, price a list containing "
            "one package of organic quinoa and one package of jasmine rice. Report the "
            "selected product names and combined public Costco.com total as a number."
        ),
        "tool": "price_shopping_list",
        "answer": {
            "items": [
                "Kirkland Signature Organic Quinoa, 4.5 lb",
                "Kirkland Signature Jasmine Rice, 25 lb",
            ],
            "estimated_total": 31.48,
        },
    },
}

TASK_TOML = """schema_version = "1.1"

[task]
name = "costco/{name}"
description = {description}
authors = []
keywords = ["mcp", "costco", "eval"]

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
name = "costco"
transport = "stdio"
command = "/opt/eval/start-mcp"
args = []
"""

INSTRUCTION = """# Task

{instruction}

Use the Costco integration tools available in this environment. All warehouse and
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
    && cd /opt/claude/plugins/costco \\
    && uv sync --frozen --no-dev

RUN python -m venv /opt/rewardkit \\
    && /opt/rewardkit/bin/pip install --no-cache-dir "harbor-rewardkit==0.1.*" \\
    && ln -s /opt/rewardkit/bin/rewardkit /usr/local/bin/rewardkit

COPY mock_server.py start-mcp /opt/eval/
RUN chmod +x /opt/eval/start-mcp

WORKDIR /app
ENV COSTCO_PRODUCT_URL=http://127.0.0.1:8091/graphql \\
    COSTCO_SEARCH_URL=http://127.0.0.1:8091/search \\
    COSTCO_WAREHOUSE_URL=http://127.0.0.1:8091/warehouses \\
    COSTCO_GEOCODE_URL=http://127.0.0.1:8091/geocode
"""

START_MCP = """#!/bin/sh
set -eu

python /opt/eval/mock_server.py >/tmp/costco-mock.log 2>&1 &
mock_pid=$!
trap 'kill "$mock_pid" 2>/dev/null || true' EXIT INT TERM

for attempt in $(seq 1 50); do
    if curl -sf http://127.0.0.1:8091/health >/dev/null; then
        cd /opt/claude/plugins/costco
        exec uv run --no-dev python -m src.server
    fi
    sleep 0.1
done

cat /tmp/costco-mock.log >&2
exit 1
"""

MOCK_SERVER = r'''#!/usr/bin/env python3
"""Deterministic local stand-in for Costco's public website endpoints."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

QUINOA = {
    "itemNumber": "1234567",
    "buyable": 1,
    "programTypes": "InWarehouse,ShipIt",
    "priceData": {"price": "18.99", "listPrice": "21.99"},
    "attributes": [
        {"key": "Brand", "value": "Kirkland Signature", "type": "string"},
        {"key": "Package Quantity", "value": "4.5 lb", "type": "string"},
    ],
    "description": {
        "shortDescription": "Kirkland Signature Organic Quinoa, 4.5 lb",
        "longDescription": "USDA organic white quinoa.",
    },
    "additionalFieldData": {"rating": "4.8", "numberOfRating": 321},
}
RICE = {
    "itemNumber": "7654321",
    "buyable": 1,
    "programTypes": "InWarehouse",
    "priceData": {"price": "12.49", "listPrice": "-1.00000"},
    "attributes": [
        {"key": "Brand", "value": "Kirkland Signature", "type": "string"},
        {"key": "Package Quantity", "value": "25 lb", "type": "string"},
    ],
    "description": {
        "shortDescription": "Kirkland Signature Jasmine Rice, 25 lb",
        "longDescription": "Long-grain jasmine rice.",
    },
    "additionalFieldData": {"rating": "4.7", "numberOfRating": 212},
}
WAREHOUSE = {
    "salesLocationId": 144,
    "name": [{"localeCode": "en-US", "value": "South San Francisco"}],
    "phone": "650-872-2021",
    "distance": 8.2,
    "address": {
        "line1": "451 S Airport Blvd",
        "city": "South San Francisco",
        "territory": "CA",
        "postalCode": "94080",
        "latitude": 37.644,
        "longitude": -122.405,
    },
    "services": [],
}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/health":
            self._send({"ok": True})
            return
        if path == "/geocode":
            self._send([{"lat": "37.7749", "lon": "-122.4194"}])
            return
        if path == "/warehouses":
            self._send({"salesLocations": [WAREHOUSE]})
            return
        self.send_error(404)

    def do_POST(self):
        size = int(self.headers.get("Content-Length", "0"))
        request = json.loads(self.rfile.read(size) or b"{}")
        if self.path == "/search":
            query = str(request.get("query") or "").lower()
            item = RICE if "rice" in query else QUINOA
            self._send(
                {
                    "searchResult": {
                        "totalCount": 1,
                        "results": [
                            {
                                "id": item["itemNumber"],
                                "product": {
                                    "title": item["description"]["shortDescription"],
                                    "brands": ["Kirkland Signature"],
                                    "categories": ["Grocery"],
                                    "attributes": {},
                                },
                            }
                        ],
                    }
                }
            )
            return
        if self.path == "/graphql":
            query = str(request.get("query") or "")
            items = []
            if QUINOA["itemNumber"] in query:
                items.append(QUINOA)
            if RICE["itemNumber"] in query:
                items.append(RICE)
            self._send({"data": {"products": {"catalogData": items}}})
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

PROCESS_CHECK = '''"""Verify that the answer came through the Costco MCP server."""

import json
import re
from pathlib import Path

from rewardkit import criterion

TRAJECTORY = Path("/logs/agent/trajectory.json")
SESSIONS = Path("/logs/agent/sessions")
EXPECTED_TOOL = "mcp__costco__{tool}"
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


@criterion(description="Agent called the expected Costco MCP tool")
def used_mcp_tool(workspace: Path) -> bool:
    return any(str(call.get("function_name") or "") == EXPECTED_TOOL for call in _calls())


@criterion(description="Agent did not bypass the Costco MCP server")
def no_direct_endpoint_access(workspace: Path) -> bool:
    calls = _calls()
    if not calls:
        return False
    for call in calls:
        if str(call.get("function_name") or "").startswith("mcp__costco__"):
            continue
        if BYPASS.search(json.dumps(call.get("arguments") or {{}})):
            return False
    return True
'''

OUTCOME_CHECK = '''"""Compare the submitted answer with deterministic fixture truth."""

import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

from rewardkit import criterion

EXPECTED = json.loads(
    r"""{expected}"""
)


def _matches(actual, expected):
    if isinstance(expected, float):
        try:
            normalized = re.sub(r"[^0-9.-]", "", str(actual))
            return Decimal(normalized) == Decimal(str(expected))
        except (InvalidOperation, TypeError, ValueError):
            return False
    if isinstance(expected, list):
        if isinstance(actual, str) and all(isinstance(item, str) for item in expected):
            if actual == ", ".join(expected):
                actual = expected
            else:
                actual = [item.strip() for item in actual.split(";")]
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


@criterion(description="Answer matches the mock catalog and warehouse data")
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
