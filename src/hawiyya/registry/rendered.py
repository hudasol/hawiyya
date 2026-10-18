"""The output of a generator for one registration (shared by G1 and G2, holds no logic)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Rendered:
    fields: dict[str, object]
    name_style: str
    log: tuple[str, ...]
