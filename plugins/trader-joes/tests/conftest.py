import pytest

from src import tools


@pytest.fixture(autouse=True)
def reset_client() -> None:
    tools.reset_state()
    yield
    tools.reset_state()
