"""Fit and freeze the scoring model on development seeds.

- EM (no labels) and the label fitted upper bound are estimated on the candidate pairs of
  development seeds 1 to 3 (G1, Tier S).
- u is initialised from random record pairs of seed 1.
- The isotonic calibrator is fitted on the EM log odds of seeds 1 to 3 with their labels.
- Calibration is checked on seeds 4 and 5, which share no family with the fitting seeds
  (households are generated per seed), so siblings never straddle the split.

Seeds 6 to 30 are left for evaluation; sealed seeds are never touched here.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from hawiyya.core.determinism import rng
from hawiyya.core.paths import RESULTS
from hawiyya.matching.compare import compare_pairs
from hawiyya.registry.build import Registry, build_registry
from hawiyya.scoring.calibration import ece, fit_isotonic, reliability
from hawiyya.scoring.em import (
    fit_anchored,
    fit_from_labels,
    informed_init,
    run_em,
    u_from_random,
    weight_gap,
)
from hawiyya.scoring.params import FSParams
from hawiyya.scoring.pipeline import Prepared, prepare
from hawiyya.scoring.scorer import Model, Scorer

FIT_SEEDS = (1, 2, 3)
CHECK_SEEDS = (4, 5)
MODEL_PATH = RESULTS / "model" / "model.json"
REPORT_PATH = RESULTS / "model" / "fit_report.json"


@dataclass(frozen=True)
class SeedData:
    seed: int
    reg: Registry
    prep: Prepared
    labels: np.ndarray


def labels_for(reg: Registry, prep: Prepared) -> np.ndarray:
    ids = prep.record_ids()
    return np.array([reg.truth.is_match(ids[i], ids[j]) for i, j in prep.pairs], dtype=bool)


def load_seed(seed: int, tier: str = "S", generator: str = "G1",
              placeholder_share: float | None = None) -> SeedData:
    reg = build_registry(seed, tier, generator=generator, placeholder_share=placeholder_share)
    prep = prepare(reg.records)
    return SeedData(seed, reg, prep, labels_for(reg, prep))


def _random_levels(d: SeedData, n: int = 40000) -> np.ndarray:
    g = rng(d.seed, "random_pairs")
    m = len(d.prep.feats)
    i = g.integers(0, m, size=n)
    j = g.integers(0, m, size=n)
    keep = i != j
    pairs = np.stack([i[keep], j[keep]], axis=1)
    return compare_pairs(d.prep.feats, pairs)


def log_odds_for(d: SeedData, params: FSParams, calibrator_dummy: Any = None) -> np.ndarray:
    from hawiyya.scoring.calibration import Calibrator

    cal = calibrator_dummy or Calibrator(np.array([0.0]), np.array([0.5]), np.array([1.0]),
                                         np.array([0.5]))
    return Scorer(Model(params, cal), d.prep.ctx.tf).score_levels(d.prep.levels, d.prep.tfv)


def train() -> tuple[Model, dict[str, Any]]:
    fit = [load_seed(s) for s in FIT_SEEDS]
    levels = np.concatenate([d.prep.levels for d in fit])
    labels = np.concatenate([d.labels for d in fit])
    u0 = u_from_random(_random_levels(fit[0]))
    plain = run_em(levels, informed_init(u0))
    anchored = fit_anchored(levels)
    lab = fit_from_labels(levels, labels)
    product = anchored.params
    lo = np.concatenate([log_odds_for(d, product) for d in fit])
    cal = fit_isotonic(lo, labels.astype(float))
    model = Model(product, cal, lab, {
        "fit_seeds": list(FIT_SEEDS), "check_seeds": list(CHECK_SEEDS), "generator": "G1",
        "tier": "S", "pairs_fitted": len(levels), "estimator": "em_anchored",
        "plain_em_params": plain.params.to_json(),
    })  # fmt: skip
    check = [load_seed(s) for s in CHECK_SEEDS]
    y_c = np.concatenate([d.labels for d in check]).astype(float)

    def check_stats(params: FSParams) -> dict[str, float]:
        c = fit_isotonic(np.concatenate([log_odds_for(d, params) for d in fit]),
                         labels.astype(float))
        lo_c = np.concatenate([log_odds_for(d, params) for d in check])
        return {"ece_calibrated": round(ece(c.predict(lo_c), y_c), 6),
                "average_precision": round(_average_precision(lo_c, y_c), 6)}  # fmt: skip

    def gap_stats(params: FSParams) -> dict[str, Any]:
        gap = weight_gap(params, lab)
        flat = [abs(v) for f in gap.values() for v in f.values()]
        return {"weight_gap_minus_labels": gap,
                "mean_absolute_weight_gap": round(float(np.mean(flat)), 4),
                "max_absolute_weight_gap": round(float(np.max(flat)), 4)}  # fmt: skip

    p_c = cal.predict(np.concatenate([log_odds_for(d, product) for d in check]))
    report = {
        "description": "Model fitting diagnostics on development seeds (not an experiment result).",
        "fit_seeds": list(FIT_SEEDS), "check_seeds": list(CHECK_SEEDS),
        "pairs_fitted": len(levels), "match_share_fitted": round(float(labels.mean()), 6),
        "product_estimator": "em_anchored",
        "plain_em": {"iterations": plain.iterations, "converged": plain.converged,
                     "lambda": round(plain.params.lam, 6), **gap_stats(plain.params),
                     **check_stats(plain.params)},
        "em_anchored": {"lambda_iterations": anchored.iterations,
                        "lambda": round(anchored.params.lam, 6),
                        **gap_stats(anchored.params), **check_stats(anchored.params)},
        "labels": {"lambda": round(lab.lam, 6), **check_stats(lab)},
        "calibration_check": {
            "pairs": len(y_c),
            "ece_product": round(ece(p_c, y_c), 6),
            "isotonic_steps": len(cal.lower),
            "reliability_product": reliability(p_c, y_c),
        },
    }  # fmt: skip
    return model, report


def _average_precision(scores: np.ndarray, y: np.ndarray) -> float:
    order = np.argsort(-scores, kind="mergesort")
    ys = y[order]
    if ys.sum() == 0:
        return 0.0
    tp = np.cumsum(ys)
    prec = tp / np.arange(1, len(ys) + 1)
    return float((prec * ys).sum() / ys.sum())


def write(model_path: Path = MODEL_PATH, report_path: Path = REPORT_PATH) -> dict[str, Any]:
    model, report = train()
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model_path.write_text(json.dumps(model.to_json(), indent=1) + "\n", encoding="utf-8",
                          newline="\n")
    report["model_version"] = model.version
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    return report


def load_model(path: Path = MODEL_PATH) -> Model:
    return Model.load(path)
