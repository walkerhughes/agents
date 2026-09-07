"""Error normalization for Target tools."""

from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any

import httpx


class TargetError(Exception):
    """Expected error with guidance suitable for an MCP response."""


def guarded_tool(function: Callable[..., Awaitable[str]]) -> Callable[..., Awaitable[str]]:
    @wraps(function)
    async def wrapped(*args: Any, **kwargs: Any) -> str:
        try:
            return await function(*args, **kwargs)
        except TargetError as exc:
            return f"Target request could not be completed: {exc}"
        except httpx.TimeoutException:
            return "Target request timed out. Try again shortly or reduce the number of items."
        except httpx.HTTPStatusError as exc:
            return f"Target returned HTTP {exc.response.status_code}. Try again shortly."
        except httpx.HTTPError as exc:
            return f"Target could not be reached: {exc}"

    return wrapped
