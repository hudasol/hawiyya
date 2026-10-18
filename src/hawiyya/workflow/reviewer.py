"""Simulated reviewer (no real person is notified or involved).

A reviewer with a given accuracy looks at a review case and answers whether the two records
are the same person; the lab supplies the ground truth through an oracle function. Each case
takes a fixed number of minutes. Used to estimate workload and residual error after review.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from hawiyya.core.determinism import rng


@dataclass(frozen=True)
class ReviewerModel:
    accuracy: float = 0.97  # ASSUMPTION
    minutes_per_case: float = 4.0  # ASSUMPTION


@dataclass(frozen=True)
class ReviewOutcome:
    cases: int
    minutes: float
    false_merges: int
    missed_duplicates: int
    correct: int


def simulate(pairs: Sequence[tuple[str, str]], oracle: Callable[[str, str], bool],
             model: ReviewerModel, seed: int) -> ReviewOutcome:
    g = rng(seed, "reviewer")
    right = g.random(len(pairs)) < model.accuracy
    fm = md = ok = 0
    for (a, b), correct in zip(pairs, right, strict=True):
        truth = oracle(a, b)
        said_match = truth if correct else not truth
        if said_match and not truth:
            fm += 1
        elif not said_match and truth:
            md += 1
        else:
            ok += 1
    return ReviewOutcome(len(pairs), round(len(pairs) * model.minutes_per_case, 3), fm, md, ok)
