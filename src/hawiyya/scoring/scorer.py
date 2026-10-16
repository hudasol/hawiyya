"""The scorer: levels and frequencies in, log odds, calibrated probability and evidence out.

The scorer receives only comparison levels, frequency values and registration records. It
never receives a truth label (see the label isolation contract).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Any

import numpy as np

from hawiyya.contract.models import EvidenceItem, PairScore
from hawiyya.matching.compare import TF_FIELDS, RecFeat, compare_pair, tf_values
from hawiyya.matching.levels import FIELD_INDEX, FIELDS
from hawiyya.normalise.record import TermFrequencies

from .calibration import Calibrator
from .params import NEUTRAL_MASK, FSParams, TfReference, tf_adjustment

TF_COLS = np.array([FIELD_INDEX[f] for f in TF_FIELDS])


@dataclass(frozen=True)
class Model:
    """Frozen model: EM parameters, the label fitted reference and the calibrator."""

    params: FSParams
    calibrator: Calibrator
    label_params: FSParams | None = None
    meta: dict[str, Any] | None = None

    @property
    def version(self) -> str:
        return self.params.version()

    def to_json(self) -> dict[str, Any]:
        return {
            "params": self.params.to_json(),
            "label_params": self.label_params.to_json() if self.label_params else None,
            "calibrator": self.calibrator.to_json(),
            "meta": self.meta or {},
        }

    @staticmethod
    def from_json(d: dict[str, Any]) -> Model:
        lp = d.get("label_params")
        return Model(FSParams.from_json(d["params"]), Calibrator.from_json(d["calibrator"]),
                     FSParams.from_json(lp) if lp else None, d.get("meta") or {})

    @staticmethod
    def load(path: Path) -> Model:
        return Model.from_json(json.loads(path.read_text(encoding="utf-8")))


def base_weights(levels: np.ndarray, params: FSParams) -> np.ndarray:
    """Per pair and field weight before frequency adjustment, shape (n, n_fields)."""
    w = params.weights()
    cols = np.arange(len(FIELDS))[None, :]
    out: np.ndarray = w[cols, levels.astype(np.int64)]
    return out


def score_arrays(levels: np.ndarray, tfv: np.ndarray, params: FSParams,
                 ref: TfReference) -> tuple[np.ndarray, np.ndarray]:
    """Vectorised log odds and the per field contributions (weights after adjustment)."""
    bw = base_weights(levels, params)
    adj = tf_adjustment(bw[:, TF_COLS], tfv, ref)
    contrib = bw.copy()
    contrib[:, TF_COLS] += adj
    log_odds: np.ndarray = params.prior_log_odds + contrib.sum(axis=1)
    return log_odds, contrib


@dataclass(frozen=True)
class Scorer:
    model: Model
    tf: TermFrequencies

    @cached_property
    def ref(self) -> TfReference:
        return TfReference.from_tables((self.tf.given, self.tf.family, self.tf.dob, self.tf.phone))

    def score_levels(self, levels: np.ndarray, tfv: np.ndarray) -> np.ndarray:
        return score_arrays(levels, tfv, self.model.params, self.ref)[0]

    def probabilities(self, log_odds: np.ndarray) -> np.ndarray:
        return self.model.calibrator.predict(log_odds)

    def pair_score(self, a: RecFeat, b: RecFeat) -> PairScore:
        """Full evidence for one pair. The evidence weights add up to the log odds."""
        lv = compare_pair(a, b)
        tfv = tf_values(a, b, lv, self.tf)
        log_odds, contrib = score_arrays(lv[None, :], tfv[None, :], self.model.params, self.ref)
        p = self.model.params
        items = []
        bw = base_weights(lv[None, :], p)[0]
        for fi, f in enumerate(FIELDS):
            li = int(lv[fi])
            neutral = bool(NEUTRAL_MASK[fi, li])
            items.append(EvidenceItem(
                field=f.name, level=f.levels[li],
                m=1.0 if neutral else float(p.m[fi, li]),
                u=1.0 if neutral else float(p.u[fi, li]),
                llr=float(bw[fi]), tf_adjustment=float(contrib[0, fi] - bw[fi]),
                weight=float(contrib[0, fi]),
                placeholder=f.levels[li] == "placeholder",
            ))  # fmt: skip
        lo_arr = np.array([log_odds[0]])
        prob = float(self.model.calibrator.predict(lo_arr)[0])
        lo, hi = self.model.calibrator.interval(lo_arr)
        a_id, b_id = sorted((a.rec.record_id, b.rec.record_id))
        return PairScore(
            record_a=a_id, record_b=b_id, prior_log_odds=p.prior_log_odds,
            log_odds=float(log_odds[0]), probability=prob,
            probability_low=float(min(lo[0], prob)), probability_high=float(max(hi[0], prob)),
            evidence=items, model_version=self.model.version,
        )  # fmt: skip
