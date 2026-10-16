"""L3 matching tests: blocking and comparison levels."""

from __future__ import annotations

import json

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from hawiyya.contract.enums import DatePrecision, IdCapture, IdKind, Sex
from hawiyya.contract.models import Record
from hawiyya.core.paths import RESULTS
from hawiyya.matching.blocking import PASSES, block, pair_completeness, record_keys
from hawiyya.matching.compare import compare_pair, features
from hawiyya.matching.levels import FIELD_INDEX, FIELDS, spec
from hawiyya.normalise.record import normalise_record, normalise_registry


def rec(rid: str, **kw: object) -> Record:
    base: dict[str, object] = dict(
        record_id=rid, facility_id="F1", name_latin="Ahmed Saeed Al Kaabi", sex=Sex.MALE,
        dob="1990-03-05", dob_precision=DatePrecision.DAY, id_value="784199012345671",
        id_kind=IdKind.EID, id_capture=IdCapture.READER, nationality="ARE",
        phone="0501234567", area="A01", registered_on="2024-01-01",
    )  # fmt: skip
    base.update(kw)
    return Record.model_validate(base)


def levels(a: Record, b: Record) -> dict[str, str]:
    lv = compare_pair(features(normalise_record(a)), features(normalise_record(b)))
    return {f.name: f.levels[int(lv[i])] for i, f in enumerate(FIELDS)}


@pytest.fixture(scope="module")
def ctx_s(reg_s):  # type: ignore[no-untyped-def]
    return normalise_registry(reg_s.records)


@pytest.mark.req("HW-L3-001", "HW-L3-007")
def test_multi_pass_union_and_metrics(ctx_s, reg_s) -> None:  # type: ignore[no-untyped-def]
    res = block(ctx_s.records)
    assert set(res.per_pass) >= {"family_year", "given_dob", "id_tail", "phone", "name_pair"}
    single = block(ctx_s.records, passes=("given_dob",))
    enc = set(map(tuple, res.pairs.tolist()))
    assert set(map(tuple, single.pairs.tolist())) <= enc
    assert len(res.pairs) > len(single.pairs)
    assert 0.99 < res.reduction_ratio < 1.0
    assert 1.0 < res.pairs_per_record < 50.0
    idx = {r.record_id: i for i, r in enumerate(ctx_s.records)}
    tp = np.array([(min(idx[a], idx[b]), max(idx[a], idx[b])) for a, b in reg_s.truth.true_pairs()])
    assert pair_completeness(res.pairs, tp, len(ctx_s.records)) > 0.95
    smoke = json.loads((RESULTS / "dev" / "blocking_smoke.json").read_text(encoding="utf-8"))
    assert {"pair_completeness", "reduction_ratio", "pairs_per_record",
            "pair_completeness_lost_to_cap"} <= set(smoke)


@pytest.mark.req("HW-L3-002")
def test_placeholders_never_block() -> None:
    a = normalise_record(rec("a", id_value="1" * 15, id_kind=IdKind.PLACEHOLDER,
                             id_capture=IdCapture.PLACEHOLDER))
    b = normalise_record(rec("b", id_value="111111111111111", id_kind=IdKind.EID,
                             id_capture=IdCapture.MANUAL))
    for r in (a, b):
        assert not [p for p, _ in record_keys(r) if p.startswith("id_")]
    x = normalise_record(rec("x", name_latin="Priya Sharma", dob="1985-07-07", phone=None,
                             id_value="1" * 15, id_kind=IdKind.PLACEHOLDER))
    y = normalise_record(rec("y", name_latin="John Smith", dob="1960-02-02", phone=None,
                             id_value="1" * 15, id_kind=IdKind.PLACEHOLDER))
    assert len(block([x, y]).pairs) == 0


@pytest.mark.req("HW-L3-003")
def test_block_cap_with_sorted_neighbourhood() -> None:
    recs = [normalise_record(rec(f"r{i}", id_value=f"7841990{i:08d}", phone=None))
            for i in range(400)]
    capped = block(recs, cap=60, window=5)
    assert capped.capped_blocks >= 1
    assert len(capped.pairs) <= 400 * 5 * len(PASSES)
    full = block(recs, cap=10**9)
    assert len(full.pairs) == 400 * 399 // 2
    assert len(capped.pairs) < len(full.pairs)


@pytest.mark.req("HW-L3-004")
def test_every_field_has_levels() -> None:
    names = {f.name for f in FIELDS}
    assert {"given", "family", "father", "dob", "sex", "identifier", "phone",
            "nationality", "area"} <= names
    lv = levels(rec("a"), rec("b"))
    assert lv["given"] == "exact" and lv["dob"] == "exact" and lv["identifier"] == "exact"
    assert levels(rec("a"), rec("b", dob="1990-05-03"))["dob"] == "transposed"
    assert levels(rec("a"), rec("b", dob="1991-03-05"))["dob"] == "digit1"
    assert levels(rec("a"), rec("b", name_latin="Ahmad Said Alkaabi"))["given"] == "skeleton"
    arabic = levels(rec("a"), rec("b", name_latin=None, name_ar="أحمد سعيد الكعبي"))
    assert arabic["given"] == "skeleton" and arabic["family"] == "skeleton"
    assert levels(rec("a"), rec("b", name_latin="A. Saeed Al Kaabi"))["given"] == "initial"
    assert levels(rec("a"), rec("b", id_value="784199012345617"))["identifier"] == "edit1"
    sub = levels(rec("a"), rec("b", dob="2025-01-01", id_kind=IdKind.MOTHER_EID,
                                 id_capture=IdCapture.SUBSTITUTE))
    assert sub["identifier"] == "shared_substitute"


@settings(max_examples=200, deadline=None)
@given(st.data())
@pytest.mark.req("HW-L3-005")
def test_levels_are_symmetric(ctx_s, data) -> None:  # type: ignore[no-untyped-def]
    recs = ctx_s.records
    i = data.draw(st.integers(0, len(recs) - 1))
    j = data.draw(st.integers(0, len(recs) - 1))
    a, b = features(recs[i]), features(recs[j])
    assert np.array_equal(compare_pair(a, b), compare_pair(b, a))


@pytest.mark.req("HW-L3-006")
def test_missing_never_turns_disagreement_into_agreement() -> None:
    a = rec("a")
    b = rec("b", dob="1975-11-20", id_value="784197512345678", sex=Sex.FEMALE)
    full = levels(a, b)
    assert full["dob"] == "conflict" and full["sex"] == "disagree"
    thin = levels(a, rec("b", dob="1975-11-20", id_value=None, id_kind=None, id_capture=None,
                         phone=None, nationality=None, area=None, sex=Sex.FEMALE))
    assert thin["dob"] == "conflict" and thin["sex"] == "disagree"
    gone = levels(a, rec("b", dob=None, dob_precision=None, sex=None))
    assert gone["dob"] == "missing" and gone["sex"] == "missing"
    for field in ("given", "family", "father"):
        assert spec(field).index("missing") > spec(field).index("initial")


@pytest.mark.req("HW-L3-008")
def test_capture_method_modifies_identifier_level() -> None:
    other = "784198812345670"
    reader = levels(rec("a"), rec("b", id_value=other))
    manual = levels(rec("a", id_capture=IdCapture.MANUAL), rec("b", id_value=other))
    assert reader["identifier"] == "different_reader"
    assert manual["identifier"] == "different_manual"
    assert FIELD_INDEX["identifier"] >= 0
