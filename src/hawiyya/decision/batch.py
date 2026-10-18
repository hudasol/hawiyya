"""Vectorised decisions over many candidate pairs (used by the lab and the review queue).

The model decision is computed for every pair from the calibrated probabilities. Guards can
only lower a LINK, so they are evaluated only for pairs whose model decision is LINK. The
result is identical to calling ``engine.decide`` pair by pair (a test checks this).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from hawiyya.contract.enums import ReasonCode
from hawiyya.contract.models import Costs, Record
from hawiyya.matching.levels import FIELDS

from .costs import DEFAULT_COSTS, LINK, REVIEW, decide_codes
from .guards import GuardInput, fired

GUARD_BITS = {code: 1 << i for i, code in enumerate(ReasonCode)}


@dataclass(frozen=True)
class BatchDecisions:
    model_codes: np.ndarray  # int8 per pair
    codes: np.ndarray  # int8 per pair, after guards
    guard_bits: np.ndarray  # int32 bitmask of guards fired (LINK pairs only)

    def guards_of(self, k: int) -> list[ReasonCode]:
        return [c for c, bit in GUARD_BITS.items() if int(self.guard_bits[k]) & bit]


def decide_batch(pairs: np.ndarray, levels: np.ndarray, contrib: np.ndarray, probs: np.ndarray,
                 records: Sequence[Record], costs: Costs = DEFAULT_COSTS) -> BatchDecisions:
    model = decide_codes(probs, costs)
    codes = model.copy()
    bits = np.zeros(len(pairs), dtype=np.int32)
    names = [f.name for f in FIELDS]
    for k in np.flatnonzero(model == LINK):
        i, j = int(pairs[k, 0]), int(pairs[k, 1])
        g = GuardInput(
            {n: FIELDS[fi].levels[int(levels[k, fi])] for fi, n in enumerate(names)},
            {n: float(contrib[k, fi]) for fi, n in enumerate(names)},
            records[i], records[j],
        )  # fmt: skip
        fg = fired(g)
        if fg:
            codes[k] = REVIEW
            for c in fg:
                bits[k] |= GUARD_BITS[c]
    return BatchDecisions(model, codes, bits)
