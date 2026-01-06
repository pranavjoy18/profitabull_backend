from datetime import datetime, time


def parse_trigger_time(value: str | None) -> time | None:
    if not value:
        return None

    try:
        return datetime.strptime(value.strip(), "%I:%M %p").time()
    except Exception:
        return None
