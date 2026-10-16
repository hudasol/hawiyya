"""Isotonic calibration of log odds into probabilities, with an interval per probability.

The idea is ported from Tahdeed ``src/tahdeed/calibrate.py`` (isotonic regression fitted on
data the model never saw). The pool adjacent violators algorithm is written here so that
each fitted step keeps its count of pairs and of matches. The interval is the central 95
percent interval of a Beta(k + 1, n - k + 1) posterior for the step that the score falls in
(k matches out of n pairs). The fitting data are development seeds, which never share a
family with the evaluation seeds.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.stats import beta as beta_dist


@dataclass(frozen=True)
class Calibrator:
    """Step function: scores at or above ``lower[i]`` (and below ``lower[i+1]``) map to block i."""

    lower: np.ndarray
    prob: np.ndarray
    n: np.ndarray
    k: np.ndarray

    def block_of(self, scores: np.ndarray) -> np.ndarray:
        idx: np.ndarray = np.searchsorted(self.lower, scores, side="right") - 1
        out: np.ndarray = np.clip(idx, 0, len(self.lower) - 1)
        return out

    def predict(self, scores: np.ndarray) -> np.ndarray:
        out: np.ndarray = self.prob[self.block_of(np.asarray(scores, dtype=float))]
        return out

    def interval(self, scores: np.ndarray, level: float = 0.95) -> tuple[np.ndarray, np.ndarray]:
        b = self.block_of(np.asarray(scores, dtype=float))
        a = (1 - level) / 2
        lo = beta_dist.ppf(a, self.k[b] + 1, self.n[b] - self.k[b] + 1)
        hi = beta_dist.ppf(1 - a, self.k[b] + 1, self.n[b] - self.k[b] + 1)
        p = self.prob[b]
        return np.minimum(lo, p), np.maximum(hi, p)

    def to_json(self) -> dict[str, Any]:
        return {"lower": self.lower.tolist(), "prob": self.prob.tolist(),
                "n": self.n.tolist(), "k": self.k.tolist(),
                "interval": "Beta(k+1, n-k+1) posterior per isotonic step, central 95%"}  # fmt: skip

    @staticmethod
    def from_json(d: dict[str, Any]) -> Calibrator:
        return Calibrator(np.array(d["lower"], dtype=float), np.array(d["prob"], dtype=float),
                          np.array(d["n"], dtype=float), np.array(d["k"], dtype=float))


def fit_isotonic(scores: np.ndarray, labels: np.ndarray) -> Calibrator:
    """Pool adjacent violators on scores sorted ascending; ties are pooled first."""
    order = np.argsort(scores, kind="mergesort")
    s = np.asarray(scores, dtype=float)[order]
    y = np.asarray(labels, dtype=float)[order]
    uniq, start = np.unique(s, return_index=True)
    sums = np.add.reduceat(y, start)
    counts = np.diff(np.append(start, len(s))).astype(float)
    lows: list[float] = []
    ks: list[float] = []
    ns: list[float] = []
    for x, k, n in zip(uniq, sums, counts, strict=True):
        lows.append(float(x))
        ks.append(float(k))
        ns.append(float(n))
        while len(ks) >= 2 and ks[-2] / ns[-2] >= ks[-1] / ns[-1]:
            k2, n2 = ks.pop(), ns.pop()
            lows.pop()
            ks[-1] += k2
            ns[-1] += n2
    k_arr, n_arr = np.array(ks), np.array(ns)
    return Calibrator(np.array(lows), k_arr / n_arr, n_arr, k_arr)


def ece(probs: np.ndarray, labels: np.ndarray, bins: int = 10) -> float:
    """Expected calibration error with equal width bins."""
    probs = np.asarray(probs, dtype=float)
    labels = np.asarray(labels, dtype=float)
    if len(probs) == 0:
        return 0.0
    edges = np.linspace(0.0, 1.0, bins + 1)
    idx = np.clip(np.digitize(probs, edges[1:-1]), 0, bins - 1)
    total = 0.0
    for b in range(bins):
        mask = idx == b
        if mask.any():
            total += mask.mean() * abs(probs[mask].mean() - labels[mask].mean())
    return float(total)


def reliability(probs: np.ndarray, labels: np.ndarray, bins: int = 10) -> list[dict[str, float]]:
    edges = np.linspace(0.0, 1.0, bins + 1)
    idx = np.clip(np.digitize(probs, edges[1:-1]), 0, bins - 1)
    out = []
    for b in range(bins):
        mask = idx == b
        if mask.any():
            out.append({"bin_low": float(edges[b]), "bin_high": float(edges[b + 1]),
                        "n": int(mask.sum()), "mean_predicted": float(probs[mask].mean()),
                        "observed": float(labels[mask].mean())})  # fmt: skip
    return out
