"""L2 normalisation tests. Arabic text is asserted on, never printed."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from hawiyya.contract.enums import DatePrecision, IdCapture, IdKind
from hawiyya.contract.models import TRUTH_FIELDS
from hawiyya.core.paths import RESULTS, ROOT
from hawiyya.normalise import dates, identifiers
from hawiyya.normalise.names import parse_name
from hawiyya.normalise.record import build_tf, normalise_registry
from hawiyya.normalise.similarity import whole_name_similarity
from hawiyya.normalise.text import (
    coarse_key,
    decode_arabizi,
    normalize_text,
    script_of,
    skeleton_word,
    string_skeleton,
)

GOLDEN = json.loads((Path(__file__).parent / "golden" / "names.json").read_text(encoding="utf-8"))


@pytest.mark.req("HW-L2-010", "HW-L2-003")
def test_golden_name_table() -> None:
    rows = GOLDEN["rows"]
    assert len(rows) >= 40
    failures = []
    for i, row in enumerate(rows):
        parsed = parse_name(row["text"])
        token = getattr(parsed, row["field"]) if parsed else None
        got = skeleton_word(token) if token else None
        if got != row["skeleton"]:
            failures.append(i)
    assert failures == [], f"golden rows failing: {failures}"


@pytest.mark.req("HW-L2-001")
def test_arabic_and_latin_normalisation() -> None:
    assert normalize_text("أحمد") == normalize_text("احمد")
    assert normalize_text("إبراهيم") == normalize_text("ابراهيم")
    assert normalize_text("مُحَمَّد") == normalize_text("محمد")
    assert normalize_text("محـــمد") == normalize_text("محمد")
    assert normalize_text("موسى") == normalize_text("موسي")
    assert normalize_text("José-Luis O'Neil") == "jose luis oneil"
    assert normalize_text("١٢٣") == "123"
    assert normalize_text("Ali​  Hassan") == "ali hassan"
    assert "ة" in normalize_text("فاطمة")


@pytest.mark.req("HW-L2-002")
def test_skeleton_coarse_and_arabizi() -> None:
    assert decode_arabizi("7amad") == "hamad"
    assert decode_arabizi("3ali") == "ali"
    assert decode_arabizi("12a") == "12a"
    assert skeleton_word("5aled") == skeleton_word("khaled") == "Xld"
    assert string_skeleton("Al Mazrouei") == string_skeleton("المزروعي")
    assert coarse_key("Gd") == coarse_key("kd") == coarse_key("jt")


@pytest.mark.req("HW-L2-013")
def test_script_detection() -> None:
    assert script_of("محمد") == "ar"
    assert script_of("Mohammed") == "en"
    assert script_of("mo7amed") == "arabizi"
    assert script_of("محمد Ali") == "mixed"
    assert script_of("123") == "none"


@pytest.mark.req("HW-L2-003")
def test_person_name_model_structure() -> None:
    p = parse_name("Dr. Mohammed bin Rashid Saeed Al Mansoori")
    assert p is not None
    assert (p.given, p.father, p.grandfather, p.family) == (
        "mohammed", "rashid", "saeed", "mansoori")
    assert p.had_connector
    one = parse_name("Priya")
    assert one is not None and one.given == "priya" and one.family is None
    ini = parse_name("Ahmed M. Al Hammadi")
    assert ini is not None and "m" in ini.initials and ini.father == "m"
    glued = parse_name("Ali Almazrouei")
    sep = parse_name("Ali Al Mazrouei")
    assert glued is not None and sep is not None and glued.family == sep.family == "mazrouei"
    alex = parse_name("John Alexander")
    assert alex is not None and alex.family == "alexander"
    assert parse_name("") is None and parse_name("  ") is None


@settings(max_examples=300, deadline=None)
@given(st.text(alphabet=st.sampled_from(list("abcdeghiklmnorstuy 37-'ًـأإآاىيئؤةحخدذرزسشصضطظعغفقكلمنهو١٢")),
               max_size=30))
@pytest.mark.req("HW-L2-009")
def test_normalisation_is_idempotent(s: str) -> None:
    once = normalize_text(s)
    assert normalize_text(once) == once
    p1 = parse_name(s)
    if p1 is not None:
        p2 = parse_name(" ".join(p1.raw_tokens))
        assert p2 is not None and p2.tokens == p1.tokens


@pytest.mark.req("HW-L2-004")
def test_date_normalisation_and_variants() -> None:
    a = dates.parse_dob("1990-03-05", DatePrecision.DAY)
    b = dates.parse_dob("1990-05-03", DatePrecision.DAY)
    c = dates.parse_dob("1991-03-05", DatePrecision.DAY)
    assert a and b and c
    assert dates.transposed(a, b) and not dates.transposed(a, c)
    assert dates.year_off_by_one(a, c)
    assert dates.digit_differences(a, c) == 1
    assert {"1990-05-03", "1989-03-05", "1991-03-05"} <= dates.variants(a)
    y = dates.parse_dob("1990-01-01", DatePrecision.YEAR)
    assert y and y.precision == DatePrecision.YEAR
    assert dates.parse_dob("1990-02-30", DatePrecision.DAY) is None
    assert dates.parse_dob(None, None) is None


@pytest.mark.req("HW-L2-005")
def test_identifier_normalisation_and_kinds() -> None:
    n = identifiers.normalise_identifier("784-1990-1234567-1", IdKind.EID, IdCapture.MANUAL)
    assert n.value == "784199012345671" and n.kind == IdKind.EID and n.valid_structure
    assert identifiers.classify("AB1234567") == IdKind.PASSPORT
    assert identifiers.classify("1234598765") == IdKind.GCC_ID
    assert identifiers.classify("784199012345671") == IdKind.EID
    bad = identifiers.normalise_identifier("784309912345671", IdKind.EID, IdCapture.MANUAL)
    assert not bad.valid_structure


@pytest.mark.req("HW-L2-006")
def test_pattern_placeholders() -> None:
    for v in ("111111111111111", "000000000000000", "784000000000000", "123456789012345"):
        assert identifiers.is_pattern_placeholder(v)
        assert identifiers.normalise_identifier(v, IdKind.EID, IdCapture.MANUAL).placeholder
    assert not identifiers.is_pattern_placeholder("784199054321987")
    d = dates.parse_dob("1900-01-01", DatePrecision.DAY)
    assert d and dates.is_pattern_placeholder(d)


@pytest.mark.req("HW-L2-007")
def test_learned_placeholders_and_report(reg_s) -> None:  # type: ignore[no-untyped-def]
    ctx = normalise_registry(reg_s.records)
    assert "784199054321987" in ctx.learned.identifiers
    assert "01-01" in ctx.learned.month_days
    rep = json.loads((RESULTS / "placeholder_detector.json").read_text(encoding="utf-8"))
    for seed in rep["per_seed"]:
        learned = seed["value_level"]["learned"]
        assert {"precision", "recall"} <= set(learned)


@pytest.mark.req("HW-L2-008")
def test_term_frequencies_from_registry(reg_s) -> None:  # type: ignore[no-untyped-def]
    ctx = normalise_registry(reg_s.records)
    tf = ctx.tf
    assert tf.n_records == len(reg_s.records)
    assert abs(sum(tf.given.values()) - 1.0) < 1e-9
    assert tf.get("given", "mhmd") > tf.get("given", "zzzz")
    small = build_tf(ctx.records[:10])
    assert small.n_records == 10


@pytest.mark.req("HW-L2-011")
def test_l2_never_reads_truth_fields() -> None:
    folder = ROOT / "src" / "hawiyya" / "normalise"
    for f in folder.glob("*.py"):
        tree = ast.parse(f.read_text(encoding="utf-8"))
        names = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
        names |= {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
        assert not names & TRUTH_FIELDS, f.name


@pytest.mark.req("HW-L2-012")
def test_vowel_aware_similarity() -> None:
    a, b, c = parse_name("Hasan Ali"), parse_name("Hassan Ali"), parse_name("Hussain Ali")
    assert a and b and c
    sab, sac = whole_name_similarity(a, b), whole_name_similarity(a, c)
    assert sab is not None and sac is not None and sab > sac
    ar = parse_name("حسن علي")
    assert ar is not None and whole_name_similarity(a, ar) is None
