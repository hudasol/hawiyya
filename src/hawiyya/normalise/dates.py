"""Date of birth normalisation with precision flags and variant checks."""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from datetime import date

from hawiyya.contract.enums import DatePrecision

# Pattern based default dates (ASSUMPTION): values that registration systems commonly fill
# in when the real date is unknown.
DEFAULT_DATES = frozenset({"1900-01-01", "1970-01-01", "2000-01-01", "1901-01-01"})


@dataclass(frozen=True)
class Dob:
    year: int
    month: int
    day: int
    precision: DatePrecision

    @property
    def iso(self) -> str:
        return f"{self.year:04d}-{self.month:02d}-{self.day:02d}"

    @property
    def is_first_of_january(self) -> bool:
        return self.month == 1 and self.day == 1


def parse_dob(value: str | None, precision: DatePrecision | None) -> Dob | None:
    """Parse an ISO date. Returns None when missing or invalid."""
    if not value:
        return None
    try:
        d = date.fromisoformat(value)
    except ValueError:
        return None
    return Dob(d.year, d.month, d.day, precision or DatePrecision.DAY)


def transposed(a: Dob, b: Dob) -> bool:
    """Day and month swapped (only meaningful when both are day precise and differ)."""
    return (a.year == b.year and a.month == b.day and a.day == b.month and a.month != a.day)


def digit_differences(a: Dob, b: Dob) -> int:
    return sum(x != y for x, y in zip(a.iso, b.iso, strict=True))


def year_off_by_one(a: Dob, b: Dob) -> bool:
    return abs(a.year - b.year) == 1 and a.month == b.month and a.day == b.day


def variants(d: Dob) -> set[str]:
    """Dates a careless entry of ``d`` could produce: transposition and year off by one."""
    out: set[str] = set()
    if d.day <= 12 and d.day != d.month:
        out.add(f"{d.year:04d}-{d.day:02d}-{d.month:02d}")
    for dy in (-1, 1):
        with contextlib.suppress(ValueError):
            out.add(date(d.year + dy, d.month, d.day).isoformat())
    return out


def is_pattern_placeholder(d: Dob) -> bool:
    return d.iso in DEFAULT_DATES
