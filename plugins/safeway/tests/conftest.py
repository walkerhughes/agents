import pytest

from src import tools


@pytest.fixture(autouse=True)
def reset_tool_state() -> None:
    tools.reset_state()
