"""Errors with messages useful to an agent and its user."""

from collections.abc import Awaitable, Callable
from functools import wraps
from typing import ParamSpec, TypeVar

import httpx

P = ParamSpec("P")
T = TypeVar("T")


class CostcoError(RuntimeError):
    """A request or response problem the caller can act on."""


def guarded_tool(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T | str]]:
    """Turn expected upstream failures into concise tool output."""

    @wraps(func)
    async def wrapped(*args: P.args, **kwargs: P.kwargs) -> T | str:
        try:
            return await func(*args, **kwargs)
        except CostcoError as exc:
            return f"Costco website error: {exc}"
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status == 403:
                return (
                    "Costco blocked this automated request (HTTP 403). Retry later or confirm the result on costco.com."
                )
            return f"Costco returned HTTP {status}. Try again later."
        except httpx.RequestError as exc:
            return f"Costco could not be reached: {exc.__class__.__name__}. Try again later."

    return wrapped
