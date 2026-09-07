"""Compare the submitted answer with deterministic fixture truth."""

import json
from pathlib import Path

from rewardkit import criterion

EXPECTED = json.loads(
    r"""{
  "name": "Costa Rica Coffee",
  "price": 9.99
}"""
)


@criterion(description="Answer matches the mock catalog and store data")
def answer_matches(workspace: Path) -> bool:
    try:
        answer = json.loads((workspace / "answer.json").read_text())
    except (OSError, json.JSONDecodeError):
        return False
    return answer == EXPECTED
