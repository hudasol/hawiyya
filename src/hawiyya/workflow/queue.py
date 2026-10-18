"""Review queue: a state machine over review cases. Reviewer actions are simulated only.

States: OPEN, ASSIGNED, CONFIRMED_MERGE_REQUEST, KEPT_APART, CROSS_REFERENCED,
NEEDS_INFORMATION. A confirmed merge request is a request to the health information
management office, not a merge; a cross reference is used when records cannot be merged.
Priority grows with the expected cost of acting without review and with the case's age.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from hawiyya.contract.enums import AuditKind, ReviewState
from hawiyya.contract.models import Costs, Decision, ReviewAction, ReviewCase
from hawiyya.core.determinism import stable_hash
from hawiyya.workflow.audit import AuditLog

S = ReviewState
ALLOWED: dict[ReviewState, frozenset[ReviewState]] = {
    S.OPEN: frozenset({S.ASSIGNED, S.NEEDS_INFORMATION}),
    S.ASSIGNED: frozenset({S.CONFIRMED_MERGE_REQUEST, S.KEPT_APART, S.CROSS_REFERENCED,
                           S.NEEDS_INFORMATION, S.OPEN}),
    S.NEEDS_INFORMATION: frozenset({S.OPEN, S.ASSIGNED}),
    S.CONFIRMED_MERGE_REQUEST: frozenset(),
    S.KEPT_APART: frozenset(),
    S.CROSS_REFERENCED: frozenset(),
}  # fmt: skip
TERMINAL = frozenset(s for s, nxt in ALLOWED.items() if not nxt)
AGE_HALF_WEIGHT_DAYS = 7.0  # ASSUMPTION: a week old case counts double


class IllegalTransition(ValueError):
    pass


def priority(p: float, costs: Costs, age_days: float) -> float:
    """Expected cost of the best automatic action (what review protects against), aged."""
    cost_now = min(costs.c_fm * (1.0 - p), costs.c_md * p)
    return round(cost_now * (1.0 + max(age_days, 0.0) / AGE_HALF_WEIGHT_DAYS), 6)


def case_id(record_a: str, record_b: str) -> str:
    a, b = sorted((record_a, record_b))
    return "C" + stable_hash([a, b], length=10).upper()


def new_case(d: Decision, created_at: str, as_of: date) -> ReviewCase:
    pair = d.evidence.pair
    age = (as_of - date.fromisoformat(created_at[:10])).days
    return ReviewCase(
        case_id=case_id(pair.record_a, pair.record_b),
        record_a=pair.record_a, record_b=pair.record_b, state=S.OPEN,
        priority=priority(pair.probability, d.costs, age),
        expected_cost=round(min(d.expected_costs.values()), 6),
        created_at=created_at, decision=d, history=[],
    )  # fmt: skip


@dataclass
class ReviewQueue:
    cases: dict[str, ReviewCase] = field(default_factory=dict)
    audit: AuditLog | None = None

    def add(self, case: ReviewCase) -> None:
        self.cases[case.case_id] = case

    def ordered(self) -> list[ReviewCase]:
        return sorted(self.cases.values(), key=lambda c: (-c.priority, c.case_id))

    def open_cases(self) -> list[ReviewCase]:
        return [c for c in self.ordered() if c.state not in TERMINAL]

    def transition(self, cid: str, to: ReviewState, actor: str, at: str,
                   note: str | None = None) -> ReviewCase:
        case = self.cases[cid]
        if to not in ALLOWED[case.state]:
            raise IllegalTransition(f"{case.state.value} to {to.value} is not allowed")
        action = ReviewAction(at=at, actor=actor, from_state=case.state, to_state=to, note=note)
        new = case.model_copy(update={"state": to, "history": [*case.history, action]})
        self.cases[cid] = new
        if self.audit is not None:
            self.audit.append(AuditKind.REVIEW_ACTION, [cid, case.record_a, case.record_b],
                              case.decision.inputs_hash, at,
                              {"from_state": case.state.value, "to_state": to.value,
                               "actor": actor})  # fmt: skip
        return new

    def workload(self) -> dict[str, int]:
        counts = {s.value: 0 for s in ReviewState}
        for c in self.cases.values():
            counts[c.state.value] += 1
        return counts
