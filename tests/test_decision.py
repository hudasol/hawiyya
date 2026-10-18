"""L5 decision tests: costs, monotonicity, guards, clustering, explanations, value of information."""

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from hawiyya.contract.enums import DatePrecision, DecisionKind, IdCapture, IdKind, ReasonCode, Sex
from hawiyya.contract.models import Costs, PairScore, Record
from hawiyya.decision.batch import decide_batch
from hawiyya.decision.cluster import cluster
from hawiyya.decision.costs import KEEP, LINK, REVIEW, decide_codes, decide_one, thresholds
from hawiyya.decision.engine import decide
from hawiyya.decision.explain import explain
from hawiyya.decision.voi import QUESTIONS, next_best_questions
from hawiyya.lab.train import load_model
from hawiyya.matching.compare import features
from hawiyya.normalise.record import apply_learned, normalise_record
from hawiyya.scoring.pipeline import prepare, score_prepared
from hawiyya.scoring.scorer import Scorer

costs_st = st.builds(
    Costs,
    c_fm=st.floats(1.0, 5000.0),
    c_md=st.floats(1.0, 500.0),
    c_r=st.floats(0.1, 50.0),
)


@pytest.fixture(scope="module")
def model():  # type: ignore[no-untyped-def]
    return load_model()


@pytest.fixture(scope="module")
def scorer(model, ctx_xs):  # type: ignore[no-untyped-def]
    return Scorer(model, ctx_xs.tf), ctx_xs


def rec(rid: str, **kw: object) -> Record:
    base: dict[str, object] = dict(
        record_id=rid, facility_id="F1", name_latin="Ahmed Saeed Al Kaabi", sex=Sex.MALE,
        dob="1990-03-05", dob_precision=DatePrecision.DAY, id_value=None, id_kind=None,
        id_capture=None, nationality="ARE", phone=None, area="A01", registered_on="2024-01-01",
    )  # fmt: skip
    base.update(kw)
    return Record.model_validate(base)


def score_of(scorer, a: Record, b: Record) -> PairScore:  # type: ignore[no-untyped-def]
    sc, ctx = scorer
    fa = features(apply_learned(normalise_record(a), ctx.learned))
    fb = features(apply_learned(normalise_record(b), ctx.learned))
    return sc.pair_score(fa, fb)  # type: ignore[no-any-return]


def forced(ps: PairScore, p: float = 0.9999) -> PairScore:
    return ps.model_copy(update={"probability": p, "probability_low": p, "probability_high": p})


@settings(max_examples=300, deadline=None)
@given(p=st.floats(0, 1), c=costs_st)
@pytest.mark.req("HW-L5-001")
def test_closed_form_thresholds_minimise_expected_cost(p: float, c: Costs) -> None:
    t = thresholds(c)
    assert t.t_link == pytest.approx(1 - c.c_r / c.c_fm)
    assert t.t_keep == pytest.approx(c.c_r / c.c_md)
    costs = {LINK: c.c_fm * (1 - p), REVIEW: c.c_r, KEEP: c.c_md * p}
    chosen = decide_one(p, c)
    assert costs[chosen] <= min(costs.values()) + 1e-9


@settings(max_examples=200, deadline=None)
@given(p1=st.floats(0, 1), p2=st.floats(0, 1), c=costs_st)
@pytest.mark.req("HW-L5-002")
def test_monotone_in_probability(p1: float, p2: float, c: Costs) -> None:
    lo, hi = sorted((p1, p2))
    assert decide_one(lo, c) <= decide_one(hi, c)


@settings(max_examples=100, deadline=None)
@given(c=costs_st, factor=st.floats(1.0, 20.0), seed=st.integers(0, 1000))
@pytest.mark.req("HW-L5-003", "HW-L5-004")
def test_raising_costs_never_adds_links_or_reviews(c: Costs, factor: float, seed: int) -> None:
    p = np.random.default_rng(seed).random(500)
    more_fm = Costs(c_fm=c.c_fm * factor, c_md=c.c_md, c_r=c.c_r)
    assert (decide_codes(p, more_fm) == LINK).sum() <= (decide_codes(p, c) == LINK).sum()
    more_r = Costs(c_fm=c.c_fm, c_md=c.c_md, c_r=c.c_r * factor)
    assert (decide_codes(p, more_r) == REVIEW).sum() <= (decide_codes(p, c) == REVIEW).sum()


@pytest.mark.req("HW-L5-005")
def test_hard_conflict_guard(scorer) -> None:  # type: ignore[no-untyped-def]
    a = rec("a", id_value="784199011111111", id_kind=IdKind.EID, id_capture=IdCapture.READER)
    b = rec("b", id_value="784199022222222", id_kind=IdKind.EID, id_capture=IdCapture.READER)
    d = decide(forced(score_of(scorer, a, b)), a, b)
    assert ReasonCode.HARD_CONFLICT in d.guards_fired and d.decision != DecisionKind.LINK
    same = rec("b", id_value="784199011111111", id_kind=IdKind.EID, id_capture=IdCapture.READER)
    d2 = decide(forced(score_of(scorer, a, same)), a, same)
    assert ReasonCode.HARD_CONFLICT not in d2.guards_fired and d2.decision == DecisionKind.LINK


@pytest.mark.req("HW-L5-006")
def test_twin_or_sibling_guard(scorer) -> None:  # type: ignore[no-untyped-def]
    a = rec("a", name_latin="Ahmed Saeed Al Kaabi")
    b = rec("b", name_latin="Khalid Saeed Al Kaabi")
    d = decide(forced(score_of(scorer, a, b)), a, b)
    assert ReasonCode.POSSIBLE_TWIN_OR_SIBLING in d.guards_fired
    assert d.decision != DecisionKind.LINK
    same = rec("b", name_latin="Ahmad Saeed Alkaabi")
    assert ReasonCode.POSSIBLE_TWIN_OR_SIBLING not in decide(
        forced(score_of(scorer, a, same)), a, same).guards_fired
    a_id = rec("a", id_value="784199033333333", id_kind=IdKind.EID, id_capture=IdCapture.READER)
    b_id = rec("b", name_latin="Khalid Saeed Al Kaabi", id_value="784199033333333",
               id_kind=IdKind.EID, id_capture=IdCapture.READER)
    assert ReasonCode.POSSIBLE_TWIN_OR_SIBLING not in decide(
        forced(score_of(scorer, a_id, b_id)), a_id, b_id).guards_fired


@pytest.mark.req("HW-L5-007")
def test_parent_child_shared_identifier_guard(scorer) -> None:  # type: ignore[no-untyped-def]
    mother = rec("m", name_latin="Fatima Ali Al Kaabi", sex=Sex.FEMALE, dob="1992-01-10",
                 id_value="784199244444444", id_kind=IdKind.EID, id_capture=IdCapture.READER)
    baby = rec("c", name_latin="Saeed Ahmed Al Kaabi", dob="2025-06-01",
               id_value="784199244444444", id_kind=IdKind.MOTHER_EID,
               id_capture=IdCapture.SUBSTITUTE)
    d = decide(forced(score_of(scorer, mother, baby)), mother, baby)
    assert ReasonCode.POSSIBLE_PARENT_CHILD_SHARED_ID in d.guards_fired
    assert d.decision != DecisionKind.LINK
    plain = rec("x", id_value="784199055555555", id_kind=IdKind.EID, id_capture=IdCapture.READER)
    plain2 = rec("y", id_value="784199055555555", id_kind=IdKind.EID, id_capture=IdCapture.MANUAL)
    assert ReasonCode.POSSIBLE_PARENT_CHILD_SHARED_ID not in decide(
        forced(score_of(scorer, plain, plain2)), plain, plain2).guards_fired


@pytest.mark.req("HW-L5-008")
def test_thin_evidence_guards(scorer) -> None:  # type: ignore[no-untyped-def]
    ph = {"id_value": "1" * 15, "id_kind": IdKind.PLACEHOLDER, "id_capture": IdCapture.PLACEHOLDER}
    a = rec("a", dob="1990-03-05", **ph)
    b = rec("b", dob="1991-07-09", **ph)
    d = decide(forced(score_of(scorer, a, b)), a, b)
    assert ReasonCode.PLACEHOLDER_ONLY in d.guards_fired and d.decision != DecisionKind.LINK
    b_ok = rec("b", dob="1990-03-05", **ph)
    assert ReasonCode.PLACEHOLDER_ONLY not in decide(
        forced(score_of(scorer, a, b_ok)), a, b_ok).guards_fired
    n1 = rec("n1", name_latin="Mohammed Ali", dob=None, dob_precision=None, area=None)
    n2 = rec("n2", name_latin="Mohammed Ali", dob=None, dob_precision=None, area=None)
    dn = decide(forced(score_of(scorer, n1, n2)), n1, n2)
    assert ReasonCode.COMMON_NAME_ONLY in dn.guards_fired and dn.decision != DecisionKind.LINK
    assert ReasonCode.COMMON_NAME_ONLY not in decide(
        forced(score_of(scorer, a, b_ok)), a, b_ok).guards_fired
    j1 = rec("j1", dob="1900-01-01")
    j2 = rec("j2", dob="1900-01-01")
    dj = decide(forced(score_of(scorer, j1, j2)), j1, j2)
    assert ReasonCode.DOB_PLACEHOLDER_SUSPECTED in dj.guards_fired
    i1 = rec("i1", dob="1900-01-01", id_value="784190066666666", id_kind=IdKind.EID,
             id_capture=IdCapture.READER)
    i2 = rec("i2", dob="1900-01-01", id_value="784190066666666", id_kind=IdKind.EID,
             id_capture=IdCapture.READER)
    assert ReasonCode.DOB_PLACEHOLDER_SUSPECTED not in decide(
        forced(score_of(scorer, i1, i2)), i1, i2).guards_fired


@pytest.mark.req("HW-L5-009")
def test_clustering_never_merges_a_contradicted_pair() -> None:
    links = [("a", "b", 0.999), ("b", "c", 0.998), ("d", "e", 0.999)]
    res = cluster(links, contradictions=[("a", "c")])
    for group in res.clusters:
        assert not {"a", "c"} <= set(group)
    assert res.conflict_edges == [("b", "c", 0.998)]
    assert ["d", "e"] in res.clusters
    plain = cluster(links, contradictions=[])
    assert ["a", "b", "c"] in plain.clusters and not plain.conflict_edges


@pytest.mark.req("HW-L5-010")
def test_three_sentence_bilingual_explanations(scorer) -> None:  # type: ignore[no-untyped-def]
    a, b = rec("a"), rec("b", name_latin="Ahmad Saeed Alkaabi")
    d = decide(score_of(scorer, a, b), a, b)
    text = explain(d, ("Scan the identity card", "x"))
    assert len(text["en"]) == 3 and len(text["ar"]) == 3
    assert all(s.strip() for s in text["en"])
    assert any("؀" <= ch <= "ۿ" for ch in " ".join(text["ar"]))


@settings(max_examples=200, deadline=None)
@given(p=st.floats(0, 1), c=costs_st)
@pytest.mark.req("HW-L5-011")
def test_value_of_information_is_never_negative(p: float, c: Costs, model) -> None:  # type: ignore[no-untyped-def]
    qs = next_best_questions(p, model.params, c)
    assert {q.key for q in qs} == set(QUESTIONS)
    assert all(q.expected_cost_reduction >= 0 for q in qs)
    assert [q.expected_cost_reduction for q in qs] == sorted(
        (q.expected_cost_reduction for q in qs), reverse=True)


@pytest.mark.req("HW-L5-012")
def test_decision_is_reproducible_from_inputs_hash(scorer) -> None:  # type: ignore[no-untyped-def]
    a, b = rec("a"), rec("b", name_latin="Ahmad Saeed Alkaabi")
    d1 = decide(score_of(scorer, a, b), a, b)
    d2 = decide(score_of(scorer, b, a), b, a)
    assert d1.inputs_hash == d2.inputs_hash
    assert d1.model_dump() == d2.model_dump()
    d3 = decide(score_of(scorer, a, b), a, b, Costs(c_fm=100, c_md=20, c_r=2))
    assert d3.inputs_hash != d1.inputs_hash


@pytest.mark.req("HW-L5-013")
def test_fail_closed_without_complete_evidence(scorer) -> None:  # type: ignore[no-untyped-def]
    a = rec("a", id_value="784199077777777", id_kind=IdKind.EID, id_capture=IdCapture.READER)
    b = rec("b", id_value="784199077777777", id_kind=IdKind.EID, id_capture=IdCapture.READER)
    ps = forced(score_of(scorer, a, b))
    assert decide(ps, a, b).decision == DecisionKind.LINK
    partial = ps.model_copy(update={"evidence": ps.evidence[:-1]})
    d = decide(partial, a, b)
    assert d.decision == DecisionKind.REVIEW and not d.evidence.complete


def test_batch_matches_pairwise(reg_xs, model) -> None:  # type: ignore[no-untyped-def]
    prep = prepare(reg_xs.records)
    sc = score_prepared(prep, model)
    bd = decide_batch(prep.pairs, prep.levels, sc.contrib, sc.prob, prep.records)
    scorer_ = Scorer(model, prep.ctx.tf)
    idx = np.random.default_rng(0).choice(len(prep.pairs), size=min(300, len(prep.pairs)),
                                          replace=False)
    for k in idx:
        i, j = map(int, prep.pairs[k])
        ps = scorer_.pair_score(prep.feats[i], prep.feats[j])
        d = decide(ps, prep.records[i], prep.records[j])
        assert d.decision.value == {0: "KEEP_APART", 1: "REVIEW", 2: "LINK"}[int(bd.codes[k])]
