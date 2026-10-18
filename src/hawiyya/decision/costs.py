"""Cost based choice between LINK, REVIEW and KEEP_APART.

With calibrated probability p that two records are the same person:

- expected cost of LINK is C_FM (1 - p) (a false merge if they are different people),
- expected cost of KEEP_APART is C_MD p (a missed duplicate if they are the same person),
- expected cost of REVIEW is C_R (a human looks at it).

LINK beats REVIEW when p > 1 - C_R / C_FM (``t_link``); KEEP_APART beats REVIEW when
p < C_R / C_MD (``t_keep``). When t_keep < t_link the review band is [t_keep, t_link]. When
t_keep >= t_link a review is never worth its cost and the choice is LINK when
p > C_FM / (C_FM + C_MD) (``t_mid``), otherwise KEEP_APART. On a boundary the less permissive
choice wins. Default costs (ASSUMPTION, swept in E9): C_FM 500, C_MD 20, C_R 2.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from hawiyya.contract.enums import DecisionKind
from hawiyya.contract.models import Costs

DEFAULT_C_FM = 500.0
DEFAULT_C_MD = 20.0
DEFAULT_C_R = 2.0
DEFAULT_COSTS = Costs(c_fm=DEFAULT_C_FM, c_md=DEFAULT_C_MD, c_r=DEFAULT_C_R)

KEEP, REVIEW, LINK = 0, 1, 2  # ordered from least to most permissive
KIND_OF = {KEEP: DecisionKind.KEEP_APART, REVIEW: DecisionKind.REVIEW, LINK: DecisionKind.LINK}
CODE_OF = {v: k for k, v in KIND_OF.items()}


@dataclass(frozen=True)
class Thresholds:
    t_link: float
    t_keep: float
    t_mid: float
    review_band: bool

    def as_dict(self) -> dict[str, float]:
        return {"t_link": self.t_link, "t_keep": self.t_keep, "t_mid": self.t_mid}


def thresholds(c: Costs) -> Thresholds:
    t_link = 1.0 - c.c_r / c.c_fm
    t_keep = c.c_r / c.c_md
    t_mid = c.c_fm / (c.c_fm + c.c_md)
    return Thresholds(t_link, t_keep, t_mid, t_keep < t_link)


def expected_costs(p: float, c: Costs) -> dict[str, float]:
    return {"LINK": c.c_fm * (1.0 - p), "REVIEW": c.c_r, "KEEP_APART": c.c_md * p}


def decide_codes(p: np.ndarray, c: Costs) -> np.ndarray:
    """Model decision codes (0 KEEP_APART, 1 REVIEW, 2 LINK) for an array of probabilities."""
    t = thresholds(c)
    p = np.asarray(p, dtype=float)
    out = np.full(p.shape, REVIEW, dtype=np.int8)
    if t.review_band:
        out[p > t.t_link] = LINK
        out[p < t.t_keep] = KEEP
    else:
        out[:] = KEEP
        out[p > t.t_mid] = LINK
    return out


def decide_one(p: float, c: Costs) -> int:
    return int(decide_codes(np.array([p]), c)[0])


def min_expected_cost(p: np.ndarray, c: Costs) -> np.ndarray:
    p = np.asarray(p, dtype=float)
    out: np.ndarray = np.minimum(np.minimum(c.c_fm * (1 - p), c.c_md * p), c.c_r)
    return out
