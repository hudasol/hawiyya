"""Batch pipeline over a registration view: normalise, block, compare, score."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np

from hawiyya.contract.models import Record
from hawiyya.matching.blocking import BlockingResult, block
from hawiyya.matching.compare import RecFeat, compare_with_tf, features
from hawiyya.normalise.record import RegistryContext, normalise_registry

from .scorer import Model, Scorer, score_arrays


@dataclass(frozen=True)
class Prepared:
    ctx: RegistryContext
    feats: tuple[RecFeat, ...]
    blocking: BlockingResult
    levels: np.ndarray
    tfv: np.ndarray
    records: tuple[Record, ...] = ()

    @property
    def pairs(self) -> np.ndarray:
        return self.blocking.pairs

    def record_ids(self) -> list[str]:
        return [r.record_id for r in self.ctx.records]


def prepare(records: Iterable[Record]) -> Prepared:
    recs = tuple(records)
    ctx = normalise_registry(recs)
    feats = tuple(features(r) for r in ctx.records)
    res = block(ctx.records)
    levels, tfv = compare_with_tf(feats, res.pairs, ctx.tf)
    return Prepared(ctx, feats, res, levels, tfv, recs)


@dataclass(frozen=True)
class Scored:
    prepared: Prepared
    log_odds: np.ndarray
    prob: np.ndarray
    contrib: np.ndarray


def score_prepared(prep: Prepared, model: Model) -> Scored:
    scorer = Scorer(model, prep.ctx.tf)
    lo, contrib = score_arrays(prep.levels, prep.tfv, model.params, scorer.ref)
    return Scored(prep, lo, scorer.probabilities(lo), contrib)
