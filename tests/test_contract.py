"""L0 contract tests."""

from __future__ import annotations

import pytest
from pydantic import BaseModel, ValidationError

from hawiyya.contract import codegen
from hawiyya.contract.enums import REASON_TEXT, DecisionKind, IdCapture, IdKind, ReasonCode
from hawiyya.contract.models import (
    ALL_MODELS,
    TRUTH_FIELDS,
    AuditEvent,
    Cluster,
    Comparison,
    Costs,
    Decision,
    EvidenceItem,
    EvidenceObject,
    ExperimentResult,
    PairScore,
    Record,
    ReviewAction,
    ReviewCase,
    Scenario,
    TruthLabels,
)


def _record(**kw: object) -> Record:
    base: dict[str, object] = dict(
        record_id="r1",
        facility_id="F1",
        name_latin="Ahmed Ali",
        sex="M",
        dob="1990-02-03",
        dob_precision="day",
        id_value="784199000000001",
        id_kind="EID",
        id_capture="reader",
        registered_on="2025-01-01",
    )
    base.update(kw)
    return Record.model_validate(base)


def _pair() -> PairScore:
    item = EvidenceItem(field="dob", level="exact", m=0.9, u=0.01, llr=4.5, weight=4.5)
    return PairScore(
        record_a="r1",
        record_b="r2",
        prior_log_odds=-5.0,
        log_odds=-0.5,
        probability=0.4,
        probability_low=0.3,
        probability_high=0.5,
        evidence=[item],
        model_version="t",
    )


def _decision() -> Decision:
    return Decision(
        decision=DecisionKind.REVIEW,
        model_decision=DecisionKind.REVIEW,
        reason_codes=[ReasonCode.INSUFFICIENT_EVIDENCE],
        guards_fired=[],
        evidence=EvidenceObject(pair=_pair(), complete=True),
        costs=Costs(c_fm=500, c_md=20, c_r=2),
        expected_costs={"LINK": 1.0},
        thresholds={"t_link": 0.9},
        inputs_hash="abc",
    )


def _examples() -> list[BaseModel]:
    d = _decision()
    return [
        _record(),
        TruthLabels(
            record_id="r1",
            person_id="p1",
            family_id="f1",
            origin_group="gulf_arab",
            facility_style="reader",
            name_style="formal_en",
        ),
        Comparison(field="dob", level="exact"),
        _pair().evidence[0],
        _pair(),
        Costs(c_fm=1, c_md=1, c_r=1),
        d.evidence,
        d,
        Cluster(cluster_id="c1", record_ids=["r1", "r2"], edges=[("r1", "r2", 0.99)]),
        ReviewAction(
            at="2025-01-01T00:00:00Z", actor="sim", from_state="OPEN", to_state="ASSIGNED"
        ),
        ReviewCase(
            case_id="k1",
            record_a="r1",
            record_b="r2",
            state="OPEN",
            priority=1.0,
            expected_cost=2.0,
            created_at="2025-01-01T00:00:00Z",
            decision=d,
        ),
        AuditEvent(
            seq=0,
            at="2025-01-01T00:00:00Z",
            kind="score",
            subject_ids=["r1"],
            inputs_hash="h",
            prev_hash="0",
            hash="1",
        ),
        Scenario(name="s", seed=1, tier="S", generator="G1"),
        ExperimentResult(experiment_id="E1", title="t", generator="G1", seeds=[1], metrics={}),
    ]


@pytest.mark.req("HW-L0-001")
def test_every_model_round_trips() -> None:
    examples = _examples()
    assert {type(e) for e in examples} == set(ALL_MODELS)
    for e in examples:
        again = type(e).model_validate_json(e.model_dump_json())
        assert again == e


@pytest.mark.req("HW-L0-002")
def test_generated_artefacts_are_fresh() -> None:
    assert codegen.stale_artefacts() == [], "run `hawiyya contract generate`"


@pytest.mark.req("HW-L0-003", "HW-L1-003")
@pytest.mark.parametrize("field", sorted(TRUTH_FIELDS))
def test_record_rejects_truth_fields(field: str) -> None:
    with pytest.raises(ValidationError):
        _record(**{field: "x"})


@pytest.mark.req("HW-L0-004")
def test_decision_without_evidence_is_rejected() -> None:
    data = _decision().model_dump()
    del data["evidence"]
    with pytest.raises(ValidationError):
        Decision.model_validate(data)


@pytest.mark.req("HW-L0-005")
def test_enums_and_bilingual_reason_text() -> None:
    assert {k.value for k in IdKind} == {
        "EID",
        "PASSPORT",
        "GCC_ID",
        "FILE_NO",
        "MOTHER_EID",
        "PLACEHOLDER",
    }
    assert {c.value for c in IdCapture} == {"reader", "manual", "substitute", "placeholder"}
    assert len(ReasonCode) == 11
    for code in ReasonCode:
        assert REASON_TEXT[code]["en"]
        ar = REASON_TEXT[code]["ar"]
        assert any("؀" <= ch <= "ۿ" for ch in ar)


@pytest.mark.req("HW-L0-006")
def test_conventions() -> None:
    with pytest.raises(ValidationError):
        EvidenceItem(field="x", level="y", m=1.5, u=0.1, llr=0, weight=0)
    with pytest.raises(ValidationError):
        _record(dob="03/02/1990")
    with pytest.raises(ValidationError):
        _record(dob_precision=None)
    with pytest.raises(ValidationError):
        AuditEvent(
            seq=0,
            at="2025-01-01 10:00",
            kind="score",
            subject_ids=[],
            inputs_hash="h",
            prev_hash="0",
            hash="1",
        )
    with pytest.raises(ValidationError):
        PairScore(
            record_a="a",
            record_b="b",
            prior_log_odds=0,
            log_odds=0,
            probability=0.5,
            probability_low=0.6,
            probability_high=0.7,
            evidence=[],
            model_version="v",
        )
