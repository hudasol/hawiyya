"""Metrics: pairwise, B cubed, calibration, intervals."""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.stats import t as t_dist

from hawiyya.decision.costs import LINK, REVIEW


def pair_counts(codes: np.ndarray, y: np.ndarray, n_true: int, n_records: int) -> dict[str, float]:
    tp = int(((codes == LINK) & y).sum())
    fp = int(((codes == LINK) & ~y).sum())
    found = int(((codes >= REVIEW) & y).sum())
    reviews = int((codes == REVIEW).sum())
    prec = tp / (tp + fp) if tp + fp else 1.0
    rec = tp / n_true if n_true else 1.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return {
        "tp": tp, "fp": fp, "found": found, "reviews": reviews,
        "link_precision": prec, "link_recall": rec, "link_f1": f1,
        "false_merges_per_10k": fp / n_records * 1e4,
        "found_recall": found / n_true if n_true else 1.0,
        "review_rate": reviews / n_records * 1e3,
    }  # fmt: skip


def bcubed(link_pairs: np.ndarray, person: np.ndarray) -> tuple[float, float]:
    """B cubed precision and recall of the clusters formed by LINK edges."""
    n = len(person)
    if len(link_pairs):
        m = coo_matrix((np.ones(len(link_pairs)), (link_pairs[:, 0], link_pairs[:, 1])),
                       shape=(n, n))  # fmt: skip
        _, comp = connected_components(m, directed=False)
    else:
        comp = np.arange(n)
    # counts of (cluster, person) pairs
    key = comp.astype(np.int64) * (int(person.max()) + 1) + person
    _, inv, both = np.unique(key, return_inverse=True, return_counts=True)
    _, cinv, csize = np.unique(comp, return_inverse=True, return_counts=True)
    _, pinv, psize = np.unique(person, return_inverse=True, return_counts=True)
    inter = both[inv]
    prec = float(np.mean(inter / csize[cinv]))
    rec = float(np.mean(inter / psize[pinv]))
    return prec, rec


def ece(p: np.ndarray, y: np.ndarray, bins: int = 10) -> float:
    if len(p) == 0:
        return 0.0
    idx = np.clip((p * bins).astype(int), 0, bins - 1)
    total = 0.0
    for b in range(bins):
        mask = idx == b
        if mask.any():
            total += mask.mean() * abs(p[mask].mean() - y[mask].mean())
    return float(total)


def mean_ci(values: Sequence[float]) -> dict[str, float]:
    v = np.asarray(values, dtype=float)
    m = float(v.mean()) if len(v) else float("nan")
    if len(v) > 1:
        half = float(t_dist.ppf(0.975, len(v) - 1) * v.std(ddof=1) / math.sqrt(len(v)))
    else:
        half = 0.0
    return {"mean": round(m, 6), "lo": round(m - half, 6), "hi": round(m + half, 6), "n": len(v)}


def wilson(k: int, n: int, z: float = 1.959964) -> dict[str, Any]:
    if n == 0:
        return {"rate": None, "lo": None, "hi": None, "k": 0, "n": 0}
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return {"rate": round(p, 6), "lo": round(max(0.0, centre - half), 6),
            "hi": round(min(1.0, centre + half), 6), "k": k, "n": n}  # fmt: skip
