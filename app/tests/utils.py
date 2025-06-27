from datetime import datetime, timedelta, timezone
from typing import Any, Dict


def iso_deadline(days_from_now: int = 0) -> str:
    """Return ISO-formatted UTC datetime string N days from now."""
    return (datetime.now(timezone.utc) + timedelta(days=days_from_now)).replace(tzinfo=None).isoformat()


def convert_datetimes(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert all datetime values in the dictionary to ISO 8601 strings."""
    converted_data = {}
    for key, value in data.items():
        if isinstance(value, datetime):
            converted_data[key] = value.isoformat()
        else:
            converted_data[key] = value
    return converted_data
