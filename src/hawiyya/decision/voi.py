"""Next best question: which single additional field would reduce the expected cost most.

For each question the form can ask, the possible answers are an agreeing and a disagreeing
level of one field. The probability of each answer is ``p m + (1 - p) u`` (renormalised over
the two answers), and the posterior after an answer follows Bayes' rule with that level's m
and u. The expected cost after asking is the answer weighted minimum expected cost. Because
the posterior is a martingale and the minimum cost is concave in p, the value of information
is never negative (a property test checks it). Only fields that exist on a registration form
are offered. This feeds a reception desk or kiosk dialogue in simulation; no hardware is built.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from hawiyya.contract.models import Costs
from hawiyya.matching.levels import FIELD_INDEX, spec
from hawiyya.scoring.params import FSParams

from .costs import min_expected_cost

# question key -> (field, agreeing level, disagreeing level, English, Arabic)
QUESTIONS: dict[str, tuple[str, str, str, str, str]] = {
    "scan_card": ("identifier", "exact", "different_reader", "Scan the identity card",
                  "امسح بطاقة الهوية"),
    "date_of_birth": ("dob", "exact", "conflict", "Ask for the date of birth",
                      "اسأل عن تاريخ الميلاد"),
    "father_name": ("father", "exact", "mismatch", "Ask for the father's name",
                    "اسأل عن اسم الأب"),
    "phone": ("phone", "exact", "different", "Ask for the phone number", "اسأل عن رقم الهاتف"),
    "passport": ("identifier", "exact", "different_manual", "Ask for the passport number",
                 "اسأل عن رقم جواز السفر"),
}  # fmt: skip


@dataclass(frozen=True)
class QuestionValue:
    key: str
    field: str
    expected_cost_reduction: float
    label_en: str
    label_ar: str


def _mu(params: FSParams, field: str, level: str) -> tuple[float, float]:
    fi = FIELD_INDEX[field]
    li = spec(field).index(level)
    return float(params.m[fi, li]), float(params.u[fi, li])


def value_of_question(p: float, params: FSParams, costs: Costs, field: str, agree: str,
                      disagree: str) -> float:
    now = float(min_expected_cost(np.array([p]), costs)[0])
    ma, ua = _mu(params, field, agree)
    md, ud = _mu(params, field, disagree)
    # Renormalise over the two answers considered.
    ms, us = ma + md, ua + ud
    ma, md, ua, ud = ma / ms, md / ms, ua / us, ud / us
    after = 0.0
    for m, u in ((ma, ua), (md, ud)):
        prob = p * m + (1 - p) * u
        if prob <= 0:
            continue
        post = p * m / prob
        after += prob * float(min_expected_cost(np.array([post]), costs)[0])
    return max(0.0, now - after)


def next_best_questions(p: float, params: FSParams, costs: Costs,
                        available: set[str] | None = None) -> list[QuestionValue]:
    """Questions ranked by expected cost reduction (largest first)."""
    out = []
    for key, (field, agree, disagree, en, ar) in QUESTIONS.items():
        if available is not None and key not in available:
            continue
        v = value_of_question(p, params, costs, field, agree, disagree)
        out.append(QuestionValue(key, field, round(v, 6), en, ar))
    return sorted(out, key=lambda q: (-q.expected_cost_reduction, q.key))
