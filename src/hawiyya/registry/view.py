"""Registration view: what a registration form contains. Safe for L2 to L5.

This module re exports only the ``Record`` model and a container that holds records. It never
exposes ground truth, family, twin, origin or facility style labels.
"""

from __future__ import annotations

from dataclasses import dataclass

from hawiyya.contract.models import Record

__all__ = ["Record", "RegistrationView"]


@dataclass(frozen=True)
class RegistrationView:
    records: tuple[Record, ...]

    def by_id(self) -> dict[str, Record]:
        return {r.record_id: r for r in self.records}

    def __len__(self) -> int:
        return len(self.records)
