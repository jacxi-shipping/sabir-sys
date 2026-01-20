"""
Jalali formatting helpers for UI presentation.

Provides `format_value_for_ui` which converts Python `date`/`datetime`
or common date strings into a Jalali-formatted string for display.
"""
from __future__ import annotations

from datetime import datetime, date
from typing import Any

import jdatetime


def format_value_for_ui(value: Any) -> str:
    """Format values for UI display using Jalali calendar for dates.

    - `datetime` -> "YYYY-MM-DD HH:MM" (Jalali)
    - `date` -> "YYYY-MM-DD" (Jalali)
    - ISO-like date/datetime strings are parsed when possible.
    - None/empty -> empty string
    - Other values -> str(value)
    """
    if value is None:
        return ""

    # datetimes
    if isinstance(value, datetime):
        j = jdatetime.datetime.fromgregorian(datetime=value)
        return f"{j.year:04d}-{j.month:02d}-{j.day:02d} {j.hour:02d}:{j.minute:02d}"

    # dates (but not datetimes)
    if isinstance(value, date):
        j = jdatetime.date.fromgregorian(date=value)
        return f"{j.year:04d}-{j.month:02d}-{j.day:02d}"

    # strings: try to parse common formats
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return ""

        # Try common strptime formats
        str_formats = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d")
        for fmt in str_formats:
            try:
                parsed = datetime.strptime(s, fmt)
                if fmt == "%Y-%m-%d":
                    j = jdatetime.date.fromgregorian(date=parsed.date())
                    return f"{j.year:04d}-{j.month:02d}-{j.day:02d}"
                else:
                    j = jdatetime.datetime.fromgregorian(datetime=parsed)
                    return f"{j.year:04d}-{j.month:02d}-{j.day:02d} {j.hour:02d}:{j.minute:02d}"
            except Exception:
                continue

        # Try ISO parser
        try:
            parsed = datetime.fromisoformat(s)
            j = jdatetime.datetime.fromgregorian(datetime=parsed)
            return f"{j.year:04d}-{j.month:02d}-{j.day:02d} {j.hour:02d}:{j.minute:02d}"
        except Exception:
            return s

    # Fallback for other types
    return str(value)


__all__ = ["format_value_for_ui"]
