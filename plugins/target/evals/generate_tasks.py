#!/usr/bin/env python3
"""Generate the Target Harbor tasks from one compact specification."""

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent

TASKS = {
    "rice-price": {
        "description": "Find the store-scoped Target price of jasmine rice.",
        "instruction": (
            "For Target store 2766 and ZIP code 94103, search for jasmine rice. "
            "Report the selected product name, TCIN, and current public price as a number."
        ),
        "tool": "search_products",
        "answer": {
            "name": "Good & Gather Organic Jasmine Rice - 32oz",
            "tcin": "88888888",
            "price": 4.99,
        },
    },
    "product-by-tcin": {
        "description": "Look up a Target product by TCIN in one store context.",
        "instruction": (
            "For Target store 2766 and ZIP code 94103, look up TCIN 88888888. "
            "Report its product name, brand, and current public price as a number."
        ),
        "tool": "get_product",
        "answer": {
            "name": "Good & Gather Organic Jasmine Rice - 32oz",
            "brand": "Good & Gather",
            "price": 4.99,
        },
    },
    "pickup-availability": {
        "description": "Find nearby Target pickup availability for a selected product.",
        "instruction": (
            "Find stores near ZIP code 94103 carrying Target TCIN 88888888. Report "
            "the nearest store ID, full store name, distance in miles, and pickup status."
        ),
        "tool": "find_stores_with_item",
        "answer": {
            "store_id": "2766",
            "name": "San Francisco Central",
            "distance_miles": 1.8,
            "pickup_status": "IN_STOCK",
        },
    },
    "shopping-list": {
        "description": "Price a two-item shopping list for one Target store.",
        "instruction": (
            "For Target store 2766 and ZIP code 94103, price a list containing one "
            "package of jasmine rice and one can of black beans. Report the selected "
            "product names and combined public Target.com total as a number."
        ),
        "tool": "price_shopping_list",
        "answer": {
            "items": [
                "Good & Gather Organic Jasmine Rice - 32oz",
                "Good & Gather Black Beans - 15oz",
            ],
            "estimated_total": 6.98,
        },
    },
}

TASK_TOML = """schema_version = "1.1"

[task]
name = "target/{name}"
description = {description}
authors = []
keywords = ["mcp", "target", "eval"]

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
name = "target"
transport = "stdio"
command = "/opt/eval/start-mcp"
args = []
"""

INSTRUCTION = """# Task

{instruction}

Use the Target integration tools available in this environment. All store and product
data must come through those tools, not shell commands, local files, direct
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
    && cd /opt/claude/plugins/target \\
    && uv sync --frozen --no-dev

RUN python -m venv /opt/rewardkit \\
    && /opt/rewardkit/bin/pip install --no-cache-dir "harbor-rewardkit==0.1.*" \\
    && ln -s /opt/rewardkit/bin/rewardkit /usr/local/bin/rewardkit

COPY mock_server.py start-mcp /opt/eval/
RUN chmod +x /opt/eval/start-mcp

WORKDIR /app
ENV TARGET_PRODUCT_URL=http://127.0.0.1:8091/product \\
    TARGET_SEARCH_URL=http://127.0.0.1:8091/search \\
    TARGET_AVAILABILITY_URL=http://127.0.0.1:8091/availability
"""

START_MCP = """#!/bin/sh
set -eu

python /opt/eval/mock_server.py >/tmp/target-mock.log 2>&1 &
mock_pid=$!
trap 'kill "$mock_pid" 2>/dev/null || true' EXIT INT TERM

for attempt in $(seq 1 50); do
    if curl -sf http://127.0.0.1:8091/health >/dev/null; then
        cd /opt/claude/plugins/target
        exec uv run --no-dev python -m src.server
    fi
    sleep 0.1
done

cat /tmp/target-mock.log >&2
exit 1
"""

MOCK_SERVER = r'''#!/usr/bin/env python3
"""Deterministic local stand-in for Target's public website endpoints."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

RICE = {
    "tcin": "88888888",
    "item": {
        "product_description": {
            "title": "Good & Gather Organic Jasmine Rice - 32oz",
            "downstream_description": "Organic long grain jasmine rice.",
            "bullet_descriptions": ["Organic", "32 ounces"],
        },
        "primary_brand": {"name": "Good & Gather"},
    },
    "price": {
        "current_retail": 4.99,
        "reg_retail": 5.49,
        "formatted_current_price": "$4.99",
        "formatted_current_price_type": "sale",
    },
    "enrichment": {"buy_url": "https://www.target.com/p/-/A-88888888", "images": {}},
    "ratings_and_reviews": {"statistics": {"rating": {"average": 4.7, "count": 120}}},
}
BEANS = {
    "tcin": "77777777",
    "item": {
        "product_description": {
            "title": "Good & Gather Black Beans - 15oz",
            "downstream_description": "Canned black beans.",
            "bullet_descriptions": ["15 ounces"],
        },
        "primary_brand": {"name": "Good & Gather"},
    },
    "price": {
        "current_retail": 1.99,
        "reg_retail": 1.99,
        "formatted_current_price": "$1.99",
        "formatted_current_price_type": "reg",
    },
    "enrichment": {"buy_url": "https://www.target.com/p/-/A-77777777", "images": {}},
    "ratings_and_reviews": {"statistics": {"rating": {"average": 4.6, "count": 80}}},
}
LOCATION = {
    "location_id": "2766",
    "distance": 1.8,
    "location_available_to_promise_quantity": 7,
    "order_pickup": {"availability_status": "IN_STOCK", "pickup_date": "2026-09-07", "guest_pick_sla": 120},
    "curbside": {"availability_status": "IN_STOCK"},
    "in_store_only": {"availability_status": "IN_STOCK"},
    "store": {
        "store_id": "2766",
        "location_name": "San Francisco Central",
        "mailing_address": {
            "address_line1": "789 Mission St",
            "city": "San Francisco",
            "state": "CA",
            "postal_code": "94103",
        },
    },
}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_GET(self):
        from urllib.parse import parse_qs, urlparse

        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        if path == "/health":
            self._send({"ok": True})
            return
        if path == "/search":
            item = BEANS if "bean" in query.get("keyword", [""])[0].lower() else RICE
            self._send(
                {
                    "data": {
                        "search": {
                            "search_response": {"metadata": {"total_results": 1}},
                            "products": [item],
                        }
                    }
                }
            )
            return
        if path == "/product":
            item = BEANS if query.get("tcin", [""])[0] == "77777777" else RICE
            self._send({"data": {"product": item}})
            return
        if path == "/availability":
            self._send({"data": {"fulfillment_fiats": {"product_id": "88888888", "locations": [LOCATION]}}})
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

PROCESS_CHECK = '''"""Verify that the answer came through the Target MCP server."""

import json
import re
from pathlib import Path

from rewardkit import criterion

TRAJECTORY = Path("/logs/agent/trajectory.json")
SESSIONS = Path("/logs/agent/sessions")
EXPECTED_TOOL = "mcp__target__{tool}"
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


@criterion(description="Agent called the expected Target MCP tool")
def used_mcp_tool(workspace: Path) -> bool:
    return any(str(call.get("function_name") or "") == EXPECTED_TOOL for call in _calls())


@criterion(description="Agent did not bypass the Target MCP server")
def no_direct_endpoint_access(workspace: Path) -> bool:
    calls = _calls()
    if not calls:
        return False
    for call in calls:
        if str(call.get("function_name") or "").startswith("mcp__target__"):
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
