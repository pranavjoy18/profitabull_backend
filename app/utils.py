from datetime import datetime, time
import json
from pathlib import Path
from typing import Any, Dict

import aiofiles


def parse_trigger_time(value: str | None) -> time | None:
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