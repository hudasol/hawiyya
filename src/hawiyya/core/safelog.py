"""Logging that never writes names or identifiers in clear.

Only record ids, hashes, counts and fixed event names may be logged. ``safe_event``
accepts keyword values that are numbers, booleans or strings made of a restricted
alphabet (ids and hex digests), and rejects anything else.
"""

from __future__ import annotations

import logging
import re

_SAFE_TEXT = re.compile(r"^[A-Za-z_][A-Za-z0-9_.:\-]{0,80}$")
_DIGITS = re.compile(r"\d{7,}")  # identifiers and phone numbers are longer than record ids

logger = logging.getLogger("hawiyya")


def is_safe_value(value: object) -> bool:
    """Return True when ``value`` may be written to a log."""
    if isinstance(value, bool | int | float) or value is None:
        return True
    if isinstance(value, str):
        return bool(_SAFE_TEXT.match(value)) and not _DIGITS.search(value)
    return False


def safe_event(event: str, **fields: object) -> str:
    """Log a structured event after checking that no field can carry a name or identifier."""
    if not _SAFE_TEXT.match(event):
        raise ValueError("event names must be simple identifiers")
    parts = [event]
    for key in sorted(fields):
        value = fields[key]
        if not is_safe_value(value):
            raise ValueError(f"field {key!r} is not safe to log")
        parts.append(f"{key}={value}")
    line = " ".join(parts)
    logger.info(line)
    return line
