"""Batch pipeline over a registration view: normalise, block, compare, score."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np

from hawiyya.contract.models import Record
from hawiyya.matching.blocking import BlockingResult, block
from hawiyya.matching.compare import RecFeat, compare_with_tf, features
from hawiyya.normalise.record import RegistryContext, normalise_registry

from .scorer import Model, Scorer


@dataclass(frozen=True)
class Prepared:
    ctx: RegistryContext
    feats: tuple[RecFeat, ...]
    blocking: BlockingResult
    levels: np.ndarray
    tfv: np.ndarray

    @property
    def pairs(self) -> np.ndarray:
        return self.blocking.pairs

    def record_ids(self) -> list[str]:
        return [r.record_id for r in self.ctx.records]


def prepare(records: Iterable[Record]) -> Prepared:
    ctx = normalise_registry(records)
    feats = tuple(features(r) for r in ctx.records)
    res = block(ctx.records)
    levels, tfv = compare_with_tf(feats, res.pairs, ctx.tf)
    return Prepared(ctx, feats, res, levels, tfv)


@dataclass(frozen=True)
class Scored:
    prepared: Prepared
    log_odds: np.ndarray
    prob: np.ndarray


def score_prepared(prep: Prepared, model: Model) -> Scored:
    scorer = Scorer(model, prep.ctx.tf)
    lo = scorer.score_levels(prep.levels, prep.tfv)
    return Scored(prep, lo, scorer.probabilities(lo))
