"""L4 scoring tests."""

from __future__ import annotations

import ast
import inspect
import json
import math

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from hawiyya.contract.models import TRUTH_FIELDS
from hawiyya.core.paths import RESULTS, ROOT
from hawiyya.lab.train import load_model
from hawiyya.matching.compare import TF_FIELDS, features
from hawiyya.matching.levels import FIELD_INDEX, FIELDS, spec
from hawiyya.normalise.record import normalise_registry
from hawiyya.scoring.calibration import ece, fit_isotonic
from hawiyya.scoring.em import fit_from_labels, informed_init, run_em
from hawiyya.scoring.params import (
    INFORMATIVE,
    MAX_LEVELS,
    NEUTRAL_MASK,
    FSParams,
    TfReference,
    normalise_rows,
)
from hawiyya.scoring.scorer import Scorer, score_arrays

NO_TF = np.full((1, len(TF_FIELDS)), np.nan)
REF = TfReference((0.01, 0.01, 0.001, 0.001))


def neutral_levels() -> np.ndarray:
    lv = np.zeros((1, len(FIELDS)), dtype=np.int8)
    for fi, f in enumerate(FIELDS):
        lv[0, fi] = f.levels.index(sorted(f.neutral)[0])
    return lv


@pytest.fixture(scope="module")
def model():  # type: ignore[no-untyped-def]
    return load_model()


@pytest.fixture(scope="module")
def scorer_s(reg_s, model):  # type: ignore[no-untyped-def]
    ctx = normalise_registry(reg_s.records)
    return Scorer(model, ctx.tf), [features(r) for r in ctx.records]


@pytest.mark.req("HW-L4-001")
def test_hand_worked_example() -> None:
    m = np.ones((len(FIELDS), MAX_LEVELS))
    u = np.ones((len(FIELDS), MAX_LEVELS))
    gi, di = FIELD_INDEX["given"], FIELD_INDEX["dob"]
    m[gi, 0], u[gi, 0] = 0.9, 0.1
    conflict = spec("dob").index("conflict")
    m[di, conflict], u[di, conflict] = 0.05, 0.6
    p = FSParams(m, u, 0.01, "test")
    lv = neutral_levels()
    lv[0, gi] = 0
    lv[0, di] = conflict
    lo, contrib = score_arrays(lv, NO_TF, p, REF)
    # ln(0.01/0.99) + ln(0.9/0.1) + ln(0.05/0.6), worked by hand:
    # -4.595120 + 2.197225 - 2.484907 = -4.882802
    assert round(float(lo[0]), 6) == -4.882802
    assert round(float(contrib[0, gi]), 6) == 2.197225
    assert round(float(contrib[0, di]), 6) == -2.484907


def _simulate(n: int, seed: int) -> tuple[np.ndarray, np.ndarray, FSParams]:
    g = np.random.default_rng(seed)
    m = np.ones((len(FIELDS), MAX_LEVELS))
    u = np.ones((len(FIELDS), MAX_LEVELS))
    for fi in range(len(FIELDS)):
        k = int(INFORMATIVE[fi].sum())
        m[fi, INFORMATIVE[fi]] = np.linspace(k, 1, k)
        u[fi, INFORMATIVE[fi]] = np.linspace(1, k, k)
    truth = FSParams(normalise_rows(m), normalise_rows(u), 0.1, "sim")
    y = g.random(n) < truth.lam
    lv = np.zeros((n, len(FIELDS)), dtype=np.int8)
    for fi in range(len(FIELDS)):
        idx = np.flatnonzero(INFORMATIVE[fi])
        pm, pu = truth.m[fi, idx], truth.u[fi, idx]
        lv[y, fi] = g.choice(idx, size=int(y.sum()), p=pm / pm.sum())
        lv[~y, fi] = g.choice(idx, size=int((~y).sum()), p=pu / pu.sum())
    return lv, y, truth


@pytest.mark.req("HW-L4-002")
def test_em_recovers_simulated_parameters() -> None:
    lv, _, truth = _simulate(60000, 1)
    u0 = normalise_rows(np.where(INFORMATIVE, 1.0, 1.0))
    res = run_em(lv, informed_init(u0, lam=0.2))
    assert res.converged
    assert abs(res.params.lam - truth.lam) < 0.02
    assert np.abs(res.params.m[INFORMATIVE] - truth.m[INFORMATIVE]).max() < 0.06


@pytest.mark.req("HW-L4-003")
def test_label_fit_and_reported_gap() -> None:
    lv, y, truth = _simulate(40000, 2)
    lab = fit_from_labels(lv, y)
    assert np.abs(lab.m[INFORMATIVE] - truth.m[INFORMATIVE]).max() < 0.03
    rep = json.loads((RESULTS / "model" / "fit_report.json").read_text(encoding="utf-8"))
    for est in ("plain_em", "em_anchored"):
        assert "weight_gap_minus_labels" in rep[est]
        assert "mean_absolute_weight_gap" in rep[est]
    assert rep["product_estimator"] == "em_anchored"


@pytest.mark.req("HW-L4-004")
def test_term_frequency_adjustment(model) -> None:  # type: ignore[no-untyped-def]
    lv = neutral_levels()
    lv[0, FIELD_INDEX["given"]] = 0
    rare = np.array([[0.0001, np.nan, np.nan, np.nan]])
    common = np.array([[0.2, np.nan, np.nan, np.nan]])
    ref = TfReference((0.02, 0.02, 0.001, 0.001))
    lo_rare = score_arrays(lv, rare, model.params, ref)[0][0]
    lo_common = score_arrays(lv, common, model.params, ref)[0][0]
    lo_none = score_arrays(lv, NO_TF, model.params, ref)[0][0]
    assert lo_rare > lo_none > lo_common
    contrib = score_arrays(lv, np.array([[0.99, np.nan, np.nan, np.nan]]), model.params, ref)[1]
    assert contrib[0, FIELD_INDEX["given"]] >= 0.0


@pytest.mark.req("HW-L4-005")
def test_placeholder_levels_contribute_exactly_zero(model) -> None:  # type: ignore[no-untyped-def]
    w = model.params.weights()
    assert np.all(w[NEUTRAL_MASK] == 0.0)
    for name in ("identifier", "dob"):
        assert w[FIELD_INDEX[name], spec(name).index("placeholder")] == 0.0
    lv = neutral_levels()
    lv[0, FIELD_INDEX["identifier"]] = spec("identifier").index("placeholder")
    lo, contrib = score_arrays(lv, NO_TF, model.params, REF)
    assert contrib[0, FIELD_INDEX["identifier"]] == 0.0
    assert lo[0] == model.params.prior_log_odds


@pytest.mark.req("HW-L4-006")
def test_calibration_isotonic_interval_and_ece(model) -> None:  # type: ignore[no-untyped-def]
    g = np.random.default_rng(3)
    s = g.normal(size=5000)
    y = (g.random(5000) < 1 / (1 + np.exp(-2 * s))).astype(float)
    cal = fit_isotonic(s, y)
    grid = np.linspace(-4, 4, 200)
    p = cal.predict(grid)
    assert np.all(np.diff(p) >= 0)
    lo, hi = cal.interval(grid)
    assert np.all(lo <= p) and np.all(p <= hi)
    assert ece(cal.predict(s), y) < 0.02
    rep = json.loads((RESULTS / "model" / "fit_report.json").read_text(encoding="utf-8"))
    assert set(rep["fit_seeds"]).isdisjoint(rep["check_seeds"])
    assert 0.0 <= rep["calibration_check"]["ece_product"] < 0.05
    assert model.meta["estimator"] == "em_anchored"


@settings(max_examples=60, deadline=None)
@given(st.data())
@pytest.mark.req("HW-L4-007", "HW-L4-009")
def test_symmetric_scores_and_evidence_sums(scorer_s, data) -> None:  # type: ignore[no-untyped-def]
    scorer, feats = scorer_s
    i = data.draw(st.integers(0, len(feats) - 1))
    j = data.draw(st.integers(0, len(feats) - 1))
    ab = scorer.pair_score(feats[i], feats[j])
    ba = scorer.pair_score(feats[j], feats[i])
    assert math.isclose(ab.log_odds, ba.log_odds, abs_tol=1e-12)
    assert ab.probability == ba.probability
    total = ab.prior_log_odds + sum(e.weight for e in ab.evidence)
    assert math.isclose(total, ab.log_odds, abs_tol=1e-9)
    assert ab.probability_low <= ab.probability <= ab.probability_high


@pytest.mark.req("HW-L4-008")
def test_monotone_in_agreement_and_conflict(model) -> None:  # type: ignore[no-untyped-def]
    w = model.params.weights()
    base = neutral_levels()
    lo0 = score_arrays(base, NO_TF, model.params, REF)[0][0]
    for fi, f in enumerate(FIELDS):
        for li, _ in enumerate(f.levels):
            if not INFORMATIVE[fi, li]:
                continue
            lv = base.copy()
            lv[0, fi] = li
            lo = score_arrays(lv, NO_TF, model.params, REF)[0][0]
            if w[fi, li] > 0:
                assert lo > lo0
            if w[fi, li] < 0:
                assert lo < lo0
    hard = ("conflict", "different_reader", "disagree", "mismatch")
    for fi, f in enumerate(FIELDS):
        for name in hard:
            if name in f.levels:
                assert w[fi, f.levels.index(name)] <= 0, f.name


@pytest.mark.req("HW-L4-010")
def test_scorer_never_receives_truth() -> None:
    for fn in (Scorer.pair_score, score_arrays, Scorer.score_levels):
        params = inspect.signature(fn).parameters
        assert not set(params) & TRUTH_FIELDS
    folder = ROOT / "src" / "hawiyya" / "scoring"
    for f in folder.glob("*.py"):
        tree = ast.parse(f.read_text(encoding="utf-8"))
        names = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
        names |= {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
        assert not names & TRUTH_FIELDS, f.name
