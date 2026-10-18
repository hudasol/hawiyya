"""Endpoint logic shared by the live API and the static snapshot builder."""

from __future__ import annotations

from typing import Any

from hawiyya.api import names
from hawiyya.api.schemas import (
    ADVISORY_NOTE,
    SYNTHETIC_NOTE,
    CandidateOut,
    CheckOut,
    NameInput,
    RegistrationInput,
    ScoreInput,
)
from hawiyya.api.state import DEMO_SEED, DEMO_TIER, get_state, is_ready
from hawiyya.contract.enums import DecisionKind
from hawiyya.contract.models import Decision, Record
from hawiyya.core.determinism import stable_hash
from hawiyya.decision.costs import DEFAULT_COSTS
from hawiyya.decision.engine import decide
from hawiyya.decision.explain import explain
from hawiyya.decision.voi import next_best_questions
from hawiyya.matching.compare import features
from hawiyya.normalise.record import apply_learned, normalise_record
from hawiyya.registry.facilities import FACILITIES
from hawiyya.scoring.scorer import Scorer
from hawiyya.workflow.check import run_check


def _envelope(payload: dict[str, Any], mode: str = "live") -> dict[str, Any]:
    return {"synthetic_note": SYNTHETIC_NOTE, "advisory_note": ADVISORY_NOTE, "mode": mode,
            **payload}


def health() -> dict[str, Any]:
    ready = is_ready()
    out: dict[str, Any] = {"status": "ok", "registry_ready": ready}
    if ready:
        out["model_version"] = get_state().model.version
    return _envelope(out)


def to_record(body: RegistrationInput, rid: str) -> Record:
    data = body.model_dump(exclude={"top"})
    if data.get("dob") and not data.get("dob_precision"):
        data["dob_precision"] = "day"
    return Record.model_validate({"record_id": rid, "facility_id": "CHECK",
                                  "registered_on": "2026-10-01", **data})


def registry_summary() -> dict[str, Any]:
    st = get_state()
    recs = st.index.ctx.records
    n = len(recs)
    ph_id = sum(1 for r in recs if r.ident.placeholder)
    ph_dob = sum(1 for r in recs if r.dob_placeholder)
    persons = len({st.registry.truth.person_of(r.record_id) for r in recs})
    return _envelope({
        "records": n,
        "facilities": [{"facility_id": f.facility_id, "style": f.style,
                        "description": f.description} for f in FACILITIES],
        "placeholder_identifier_share": round(ph_id / n, 4),
        "suspected_default_dob_share": round(ph_dob / n, 4),
        "data_source": st.registry.meta["data_source"],
        "seed": DEMO_SEED, "tier": DEMO_TIER,
        "model_version": st.model.version,
        "synthetic_ground_truth": {
            "label": "synthetic ground truth",
            "persons": persons,
            "duplicate_record_share": round(1 - persons / n, 4),
        },
    })  # fmt: skip


def check(body: RegistrationInput) -> CheckOut:
    st = get_state()
    rid = "NEW" + stable_hash(body.model_dump(mode="json"), length=8).upper()
    rec = to_record(body, rid)
    res = run_check(st.index, st.model, rec, top=body.top)
    cands = []
    nbq: list[dict[str, Any]] | None = None
    for c in res.candidates:
        d = decide(c.score, rec, c.record, DEFAULT_COSTS)
        questions = None
        if d.decision == DecisionKind.REVIEW:
            questions = next_best_questions(c.score.probability, st.model.params, DEFAULT_COSTS)
            if nbq is None:
                nbq = [vars(q) for q in questions]
        top_q = (questions[0].label_en, questions[0].label_ar) if questions else None
        cands.append(CandidateOut(record=c.record.model_dump(mode="json"), score=c.score,
                                  decision=decision_payload(d, top_q)))  # fmt: skip
    return CheckOut(ok=res.ok, n_scored=res.n_scored, candidates=cands, note=res.note,
                    next_best_question=nbq)  # fmt: skip


def decision_payload(d: Decision, top_q: tuple[str, str] | None = None) -> dict[str, Any]:
    out = d.model_dump(mode="json", exclude={"evidence"})
    out["explanation"] = explain(d, top_q)
    return out


def score(body: ScoreInput) -> dict[str, Any]:
    st = get_state()
    ra, rb = to_record(body.a, "A"), to_record(body.b, "B")
    a = features(apply_learned(normalise_record(ra), st.index.ctx.learned))
    b = features(apply_learned(normalise_record(rb), st.index.ctx.learned))
    ps = Scorer(st.model, st.index.ctx.tf).pair_score(a, b)
    d = decide(ps, ra, rb, DEFAULT_COSTS)
    return _envelope({"score": ps.model_dump(mode="json"), "decision": decision_payload(d)})


def names_analyse(body: NameInput) -> dict[str, Any]:
    return _envelope(names.analyse(body.name, body.other))
