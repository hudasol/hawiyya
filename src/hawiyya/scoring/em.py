"""Estimation of m, u and lambda: unsupervised EM and a label fitted upper bound.

EM assumes conditional independence between fields given the match status. That assumption
is false here (siblings share family and father names, phones and areas), so EM can settle on
"same household" rather than "same person". The label fit is reported beside it so the gap is
visible, and calibration (fitted with labels on development data) repairs the scale.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from hawiyya.matching.levels import FIELDS

from .params import INFORMATIVE, MAX_LEVELS, FSParams, normalise_rows


def _onehot_counts(levels: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """Weighted level counts per field: shape (n_fields, MAX_LEVELS)."""
    out = np.zeros((len(FIELDS), MAX_LEVELS))
    for fi in range(len(FIELDS)):
        out[fi] = np.bincount(levels[:, fi], weights=weights, minlength=MAX_LEVELS)[:MAX_LEVELS]
    return out


def informed_init(u_random: np.ndarray, lam: float = 0.05) -> FSParams:
    """Initial m from the level order (strong agreement likely for matches) and u from random
    pairs."""
    m = np.zeros((len(FIELDS), MAX_LEVELS))
    for fi, f in enumerate(FIELDS):
        informative = [li for li in range(len(f.levels)) if INFORMATIVE[fi, li]]
        for rank, li in enumerate(informative):
            m[fi, li] = 0.6 ** rank
    return FSParams(normalise_rows(m), normalise_rows(u_random), lam, "em")


def u_from_random(levels_random: np.ndarray) -> np.ndarray:
    counts = _onehot_counts(levels_random, np.ones(len(levels_random))) + 0.5
    return normalise_rows(counts)


@dataclass(frozen=True)
class EMResult:
    params: FSParams
    iterations: int
    converged: bool
    log_likelihood: float


def _log_lik_terms(levels: np.ndarray, p: FSParams) -> tuple[np.ndarray, np.ndarray]:
    lm = np.zeros(len(levels))
    lu = np.zeros(len(levels))
    logm, logu = np.log(p.m), np.log(p.u)
    for fi in range(len(FIELDS)):
        col = levels[:, fi]
        inf = INFORMATIVE[fi, col]
        lm += np.where(inf, logm[fi, col], 0.0)
        lu += np.where(inf, logu[fi, col], 0.0)
    return lm, lu


def run_em(levels: np.ndarray, init: FSParams, max_iter: int = 200, tol: float = 1e-7,
           fix_u: bool = False) -> EMResult:
    """Standard two class EM over discrete levels. Neutral levels are skipped."""
    p = init
    prev = -np.inf
    ll = -np.inf
    iterations = 0
    converged = False
    for it in range(1, max_iter + 1):
        iterations = it
        lm, lu = _log_lik_terms(levels, p)
        a = np.log(p.lam) + lm
        b = np.log(1.0 - p.lam) + lu
        mx = np.maximum(a, b)
        norm = mx + np.log(np.exp(a - mx) + np.exp(b - mx))
        g = np.exp(a - norm)
        ll = float(norm.sum())
        lam = float(np.clip(g.mean(), 1e-6, 1 - 1e-6))
        m = normalise_rows(_onehot_counts(levels, g) + 1e-3)
        u = p.u if fix_u else normalise_rows(_onehot_counts(levels, 1.0 - g) + 1e-3)
        p = FSParams(m, u, lam, "em")
        if abs(ll - prev) < tol * max(1.0, abs(ll)):
            converged = True
            break
        prev = ll
    return EMResult(p, iterations, converged, ll)


def _lv(field: str, level: str) -> tuple[int, int]:
    fi = next(i for i, f in enumerate(FIELDS) if f.name == field)
    return fi, FIELDS[fi].levels.index(level)


def fit_anchored(levels: np.ndarray, max_iter: int = 200) -> EMResult:
    """Label free estimation from deterministic anchors, then EM for lambda only.

    - m for every field except the identifier: level shares among pairs whose identifiers
      agree exactly (a non placeholder, non substitute value).
    - m for the identifier: among pairs whose given and family names agree (exact or
      skeleton) and whose dates of birth agree exactly.
    - u for every field except the identifier: among pairs whose identifiers are different
      values of the same kind (these include siblings and other hard negatives).
    - u for the identifier: among pairs whose dates of birth conflict and given names differ.
    - lambda: EM with m and u held fixed.
    No ground truth label is used.
    """
    fid, ex = _lv("identifier", "exact")
    _, dm = _lv("identifier", "different_manual")
    _, dr = _lv("identifier", "different_reader")
    fg, g_ex = _lv("given", "exact")
    ff, _ = _lv("family", "exact")
    _, g_sk = _lv("given", "skeleton")
    fd, d_ex = _lv("dob", "exact")
    _, d_cf = _lv("dob", "conflict")
    _, g_mm = _lv("given", "mismatch")
    a_m = levels[:, fid] == ex
    a_u = np.isin(levels[:, fid], [dm, dr])
    b_m = (np.isin(levels[:, fg], [g_ex, g_sk]) & np.isin(levels[:, ff], [g_ex, g_sk])
           & (levels[:, fd] == d_ex))  # fmt: skip
    b_u = (levels[:, fd] == d_cf) & (levels[:, fg] == g_mm)
    m = _onehot_counts(levels[a_m], np.ones(int(a_m.sum()))) + 0.5
    u = _onehot_counts(levels[a_u], np.ones(int(a_u.sum()))) + 0.5
    m[fid] = _onehot_counts(levels[b_m], np.ones(int(b_m.sum())))[fid] + 0.5
    u[fid] = _onehot_counts(levels[b_u], np.ones(int(b_u.sum())))[fid] + 0.5
    init = FSParams(normalise_rows(m), normalise_rows(u), 0.05, "em_anchored")
    lm, lu = _log_lik_terms(levels, init)
    lam = 0.05
    ll = -np.inf
    iterations = 0
    for it in range(1, max_iter + 1):
        iterations = it
        a = np.log(lam) + lm
        b = np.log(1.0 - lam) + lu
        mx = np.maximum(a, b)
        norm = mx + np.log(np.exp(a - mx) + np.exp(b - mx))
        new = float(np.clip(np.exp(a - norm).mean(), 1e-6, 1 - 1e-6))
        ll = float(norm.sum())
        if abs(new - lam) < 1e-9:
            lam = new
            break
        lam = new
    p = FSParams(init.m, init.u, lam, "em_anchored")
    return EMResult(p, iterations, iterations < max_iter, ll)


def fit_from_labels(levels: np.ndarray, is_match: np.ndarray) -> FSParams:
    """m and u from labelled pairs with add one half smoothing (the upper bound)."""
    w = is_match.astype(float)
    m = normalise_rows(_onehot_counts(levels, w) + 0.5)
    u = normalise_rows(_onehot_counts(levels, 1.0 - w) + 0.5)
    lam = float(np.clip(w.mean(), 1e-6, 1 - 1e-6))
    return FSParams(m, u, lam, "labels")


def weight_gap(a: FSParams, b: FSParams) -> dict[str, dict[str, float]]:
    """Per field and level difference of weights (a minus b), informative levels only."""
    wa, wb = a.weights(), b.weights()
    out: dict[str, dict[str, float]] = {}
    for fi, f in enumerate(FIELDS):
        out[f.name] = {lv: round(float(wa[fi, li] - wb[fi, li]), 4)
                       for li, lv in enumerate(f.levels) if INFORMATIVE[fi, li]}  # fmt: skip
    return out
