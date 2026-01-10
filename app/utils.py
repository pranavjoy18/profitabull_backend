from datetime import datetime 
import functools
import json
from pathlib import Path
import time
from typing import Any, Awaitable, Callable, Dict, TypeVar, Union

import aiofiles


T = TypeVar("T")

def time_async(
    label: str | None = None
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """
    Decorator to time async functions.

    Usage:
        @time_async()
        async def foo(): ...

        @time_async("NSE EOD ingestion")
        async def bar(): ...
    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        name = label or func.__name__

        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            start = time.perf_counter()
            try:
                return await func(*args, **kwargs)
            finally:
                end = time.perf_counter()
                elapsed = end - start
                print(f"⏱️ {name} took {elapsed:.2f}s")

        return wrapper

    return decorator

def parse_trigger_time(value: str | None) -> Union[datetime.time,None]  :
    if not value:
        return None

    try:
        return datetime.strptime(value.strip(), "%I:%M %p").time()
    except Exception:
        return None

async def write_json_async(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")

    async with aiofiles.open(tmp, "w", encoding="utf-8") as f:
        await f.write(json.dumps(data, indent=2))

    tmp.replace(path)