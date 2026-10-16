"""Fellegi Sunter parameters and the per level weights.

For field f at level l the weight is ``ln(m[f][l] / u[f][l])`` (natural log). Neutral levels
(missing, placeholder, not comparable) have a weight of exactly zero by construction: they
are excluded from estimation and never looked up. A pair's log odds is the prior log odds
plus the sum of its field weights plus the term frequency adjustments.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np

from hawiyya.core.determinism import stable_hash
from hawiyya.matching.levels import AGREEMENT_LEVELS, DISAGREEMENT_LEVELS, FIELDS

MAX_LEVELS = max(len(f.levels) for f in FIELDS)
NEUTRAL_MASK = np.zeros((len(FIELDS), MAX_LEVELS), dtype=bool)
VALID_MASK = np.zeros((len(FIELDS), MAX_LEVELS), dtype=bool)
for _fi, _f in enumerate(FIELDS):
    for _li, _lv in enumerate(_f.levels):
        VALID_MASK[_fi, _li] = True
        NEUTRAL_MASK[_fi, _li] = _lv in _f.neutral
INFORMATIVE = VALID_MASK & ~NEUTRAL_MASK
DISAGREE_MASK = np.zeros_like(VALID_MASK)
AGREE_MASK = np.zeros_like(VALID_MASK)
for _fi, _f in enumerate(FIELDS):
    for _li, _lv in enumerate(_f.levels):
        DISAGREE_MASK[_fi, _li] = _lv in DISAGREEMENT_LEVELS
        AGREE_MASK[_fi, _li] = _lv in AGREEMENT_LEVELS


@dataclass(frozen=True)
class FSParams:
    """m and u per (field, level) as arrays of shape (n_fields, MAX_LEVELS), and lambda.

    Within each field, m and u sum to one over the informative levels.
    """

    m: np.ndarray
    u: np.ndarray
    lam: float
    source: str  # "em" or "labels"

    @property
    def prior_log_odds(self) -> float:
        return math.log(self.lam / (1.0 - self.lam))

    def raw_weights(self) -> np.ndarray:
        w = np.zeros_like(self.m)
        w[INFORMATIVE] = np.log(self.m[INFORMATIVE] / self.u[INFORMATIVE])
        return w

    def weights(self) -> np.ndarray:
        """Weights with sign constraints: disagreement levels at most zero, full agreement
        levels at least zero. Estimation on blocked candidate pairs can otherwise make, for
        example, a family name mismatch look like evidence for a match."""
        w = self.raw_weights()
        w[DISAGREE_MASK] = np.minimum(w[DISAGREE_MASK], 0.0)
        w[AGREE_MASK] = np.maximum(w[AGREE_MASK], 0.0)
        return w

    def to_json(self) -> dict[str, Any]:
        out: dict[str, Any] = {"lambda": self.lam, "source": self.source, "fields": {}}
        for fi, f in enumerate(FIELDS):
            out["fields"][f.name] = {
                lv: {"m": float(self.m[fi, li]), "u": float(self.u[fi, li]),
                     "neutral": bool(NEUTRAL_MASK[fi, li])}
                for li, lv in enumerate(f.levels)
            }  # fmt: skip
        return out

    @staticmethod
    def from_json(d: dict[str, Any]) -> FSParams:
        m = np.ones((len(FIELDS), MAX_LEVELS))
        u = np.ones((len(FIELDS), MAX_LEVELS))
        for fi, f in enumerate(FIELDS):
            for li, lv in enumerate(f.levels):
                m[fi, li] = d["fields"][f.name][lv]["m"]
                u[fi, li] = d["fields"][f.name][lv]["u"]
        return FSParams(m, u, float(d["lambda"]), str(d["source"]))

    def version(self) -> str:
        return stable_hash(self.to_json(), length=12)


def normalise_rows(a: np.ndarray, floor: float = 1e-6) -> np.ndarray:
    """Clip and renormalise each field's informative levels to sum to one."""
    out = np.where(INFORMATIVE, np.maximum(a, floor), 1.0)
    for fi in range(out.shape[0]):
        mask = INFORMATIVE[fi]
        out[fi, mask] = out[fi, mask] / out[fi, mask].sum()
    return out


# ----------------------------------------------------------------------------- frequency

TF_FIELD_NAMES = ("given", "family", "dob", "phone")
TF_CLIP = 2.0  # ASSUMPTION: bound on any single frequency adjustment (natural log units)


@dataclass(frozen=True)
class TfReference:
    """Frequency weighted mean frequency per TF field (the value at which the adjustment is
    zero). Computed from the registry's own term frequency tables."""

    tf_bar: tuple[float, float, float, float]

    @staticmethod
    def from_tables(tables: tuple[dict[str, float], ...]) -> TfReference:
        bars = []
        for t in tables:
            v = np.array(list(t.values())) if t else np.array([1.0])
            bars.append(float((v**3).sum() / (v**2).sum()))
        return TfReference((bars[0], bars[1], bars[2], bars[3]))


def tf_adjustment(base_weights: np.ndarray, tfv: np.ndarray, ref: TfReference) -> np.ndarray:
    """Adjustment ``ln(tf_bar / tf)`` per TF field, clipped, and floored so that an agreeing
    level with a positive weight never ends below zero.

    ``base_weights`` holds each pair's weight for the four TF fields (n, 4); ``tfv`` the
    frequency of the agreeing value or NaN (n, 4). Returns adjustments (n, 4).
    """
    bars = np.array(ref.tf_bar)
    with np.errstate(divide="ignore", invalid="ignore"):
        adj = np.log(bars[None, :] / tfv)
    adj = np.clip(np.nan_to_num(adj, nan=0.0), -TF_CLIP, TF_CLIP)
    floor = np.where(base_weights > 0, -base_weights, -np.inf)
    adj = np.maximum(adj, floor)
    adj[np.isnan(tfv)] = 0.0
    out: np.ndarray = adj
    return out
