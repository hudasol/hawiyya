"""Decision engine: a calibrated pair score and two registration records in, a Decision out.

Order: model decision from costs, then guards (which can only lower it), then the fail
closed rule (no LINK without a complete evidence table). The inputs hash covers both records,
the model version and the costs, so a stored decision can be reproduced.
"""

from __future__ import annotations

from hawiyya.contract.enums import DecisionKind, ReasonCode
from hawiyya.contract.models import Costs, Decision, EvidenceObject, PairScore, Record
from hawiyya.core.determinism import stable_hash
from hawiyya.matching.levels import FIELDS

from .costs import (
    CODE_OF,
    DEFAULT_COSTS,
    KIND_OF,
    LINK,
    REVIEW,
    decide_one,
    expected_costs,
    thresholds,
)
from .guards import GuardInput, fired

STRONG = 2.0  # a single field contribution this large (natural log units) counts as strong


def evidence_complete(score: PairScore) -> bool:
    """Every field has an evidence item and the items add up to the log odds."""
    fields = {e.field for e in score.evidence}
    total = score.prior_log_odds + sum(e.weight for e in score.evidence)
    return fields == {f.name for f in FIELDS} and abs(total - score.log_odds) < 1e-6


def inputs_hash(a: Record, b: Record, model_version: str, costs: Costs) -> str:
    ra, rb = sorted((a.model_dump(mode="json"), b.model_dump(mode="json")),
                    key=lambda r: r["record_id"])  # fmt: skip
    return stable_hash({"a": ra, "b": rb, "model": model_version,
                        "costs": costs.model_dump(mode="json")}, length=24)  # fmt: skip


def _reasons(score: PairScore, decision: int, guards: list[ReasonCode]) -> list[ReasonCode]:
    lv = {e.field: e.level for e in score.evidence}
    w = {e.field: e.weight for e in score.evidence}
    out: list[ReasonCode] = []
    if lv.get("identifier") == "exact" and w.get("identifier", 0.0) > 0:
        out.append(ReasonCode.STRONG_ID_AGREEMENT)
    if (lv.get("given") in ("exact", "skeleton") and lv.get("family") in ("exact", "skeleton")
            and lv.get("dob") == "exact"):  # fmt: skip
        out.append(ReasonCode.STRONG_DEMOGRAPHIC_AGREEMENT)
    if max(w.values()) >= STRONG and min(w.values()) <= -STRONG:
        out.append(ReasonCode.CONFLICTING_EVIDENCE)
    if decision == REVIEW and not guards and ReasonCode.CONFLICTING_EVIDENCE not in out:
        out.append(ReasonCode.INSUFFICIENT_EVIDENCE)
    return out + [g for g in guards if g not in out]


def decide(score: PairScore, a: Record, b: Record, costs: Costs = DEFAULT_COSTS) -> Decision:
    model_code = decide_one(score.probability, costs)
    # Guards can only lower a LINK, so they are evaluated (and reported) only for model LINKs.
    guards = fired(GuardInput.from_score(score, a, b)) if model_code == LINK else []
    code = model_code
    if code == LINK and guards:
        code = REVIEW
    complete = evidence_complete(score)
    if code == LINK and not complete:
        code = REVIEW  # fail closed for merges
    t = thresholds(costs)
    return Decision(
        decision=KIND_OF[code],
        model_decision=KIND_OF[model_code],
        reason_codes=_reasons(score, code, guards),
        guards_fired=guards,
        evidence=EvidenceObject(pair=score, complete=complete, guards_fired=guards),
        costs=costs,
        expected_costs=expected_costs(score.probability, costs),
        thresholds=t.as_dict(),
        inputs_hash=inputs_hash(a, b, score.model_version, costs),
    )


def code_of(kind: DecisionKind) -> int:
    return CODE_OF[kind]
