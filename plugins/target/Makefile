.PHONY: check lint format typecheck test coverage selftest validate-process evals

check: lint typecheck selftest validate-process test

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff check --fix .
	uv run ruff format .

typecheck:
	uv run mypy src

selftest:
	uv run python -c "from src.server import mcp; assert len(mcp._tool_manager._tools) == 4"
	uv run python evals/check_reward.py --selftest

validate-process:
	uv run python evals/validate_process_local.py

evals:
	uv run bash evals/run_evals.sh

test:
	uv run pytest -m unit

coverage:
	uv run pytest --cov=src --cov-report=term-missing
