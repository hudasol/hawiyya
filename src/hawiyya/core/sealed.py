"""Sealed seed guard.

Development seeds are 1 to 30. Sealed seeds 1001 to 1030 may be generated only inside
``sealed_access()``, which only ``hawiyya eval --sealed`` enters. Any other attempt raises.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from hawiyya.core.errors import SealedSeedError

DEV_SEEDS = tuple(range(1, 31))
SEALED_SEEDS = tuple(range(1001, 1031))
_state = {"open": False}


def is_sealed(seed: int) -> bool:
    return seed in SEALED_SEEDS


def check_seed(seed: int) -> None:
    if is_sealed(seed) and not _state["open"]:
        raise SealedSeedError(f"seed {seed} is sealed; only `hawiyya eval --sealed` may use it")


@contextmanager
def sealed_access() -> Iterator[None]:
    _state["open"] = True
    try:
        yield
    finally:
        _state["open"] = False
