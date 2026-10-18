"""L7 lab tests: G2, baselines, metrics, strata, gold set, purity, origin isolation, sealing."""

from __future__ import annotations

import ast
import re

import numpy as np
import pytest

from hawiyya.core.paths import ROOT
from hawiyya.lab import baselines as B
from hawiyya.lab.experiments import SYSTEMS, Fitted, evaluate_seed, run_suite
from hawiyya.lab.gold import load_gold, run_gold
from hawiyya.lab.metrics import bcubed, ece, mean_ci, pair_counts, wilson
from hawiyya.lab.train import labels_for, load_model
from hawiyya.registry.build import build_registry, registry_bytes
from hawiyya.scoring.pipeline import prepare, score_prepared


@pytest.fixture(scope="module")
def fitted(reg_xs):  # type: ignore[no-untyped-def]
    model = load_model()
    prep = prepare(reg_xs.records)
    gbm = B.fit_gbm(prep.levels, prep.tfv, labels_for(reg_xs, prep))
    return Fitted(model, model, gbm)


@pytest.fixture(scope="module")
def seed_result(fitted):  # type: ignore[no-untyped-def]
    return evaluate_seed({"seed": 5, "tier": "XS", "generator": "G1", "systems": SYSTEMS,
                          "strata": True, "cap_cost": True, "sweep": True, "fitted": fitted})


@pytest.mark.req("HW-L7-001")
def test_g2_is_deterministic_and_different_from_g1() -> None:
    a = build_registry(13, "XS", generator="G2")
    b = build_registry(13, "XS", generator="G2")
    g1 = build_registry(13, "XS", generator="G1")
    assert registry_bytes(a) == registry_bytes(b)
    assert registry_bytes(a) != registry_bytes(g1)
    assert a.meta["generator"] == "G2"
    styles = {lab.name_style for lab in a.truth.labels.values()}
    assert all(s.startswith("g2_") for s in styles)
    tags = {t for lab in a.truth.labels.values() for t in lab.corruption_log}
    assert {"name:keyboard", "name:swap"} <= tags
    # Same people underneath, so the comparison isolates rendering.
    assert {x.person_id for x in a.truth.labels.values()} == {
        x.person_id for x in g1.truth.labels.values()}


@pytest.mark.req("HW-L7-002")
def test_baselines_run_on_the_same_pairs(reg_xs, fitted) -> None:  # type: ignore[no-untyped-def]
    prep = prepare(reg_xs.records)
    sc = score_prepared(prep, fitted.model)
    u = B.build_universe(prep)
    outs = [B.b0_eid_exact(u, prep.records), B.b1_name_dob_exact(u, prep.records),
            B.b2_fuzzy_raw(u, prep.records), B.b3_latin_only(u, prep, fitted.b3),
            B.b4_forced(u, sc), B.b5_hawiyya(u, prep, sc), B.b6_gbm(u, prep, fitted.gbm)]
    assert all(len(o) == len(u.pairs) for o in outs)
    cand = B.encode(prep.pairs[:, 0], prep.pairs[:, 1], u.n)
    assert np.isin(cand, u.codes).all()
    assert (u.cand_index >= 0).sum() == len(prep.pairs)


@pytest.mark.req("HW-L7-003")
def test_metrics() -> None:
    y = np.array([True, True, False, False])
    codes = np.array([2, 1, 2, 0], dtype=np.int8)
    m = pair_counts(codes, y, n_true=3, n_records=100)
    assert m["tp"] == 1 and m["fp"] == 1 and m["found"] == 2
    assert m["link_precision"] == 0.5 and m["link_recall"] == pytest.approx(1 / 3)
    assert m["false_merges_per_10k"] == 100.0 and m["review_rate"] == 10.0
    person = np.array([0, 0, 1, 2])
    p, r = bcubed(np.array([[0, 1]]), person)
    assert p == 1.0 and r == 1.0
    p2, _ = bcubed(np.array([[0, 1], [1, 2]]), person)
    assert p2 < 1.0
    assert ece(np.array([0.0, 1.0]), np.array([0.0, 1.0])) == 0.0
    ci = mean_ci([1.0, 2.0, 3.0])
    assert ci["lo"] < ci["mean"] == 2.0 < ci["hi"]
    w = wilson(5, 10)
    assert w["lo"] < 0.5 < w["hi"]


@pytest.mark.req("HW-L7-004")
def test_strata_add_up_to_totals(seed_result) -> None:  # type: ignore[no-untyped-def]
    st = seed_result["strata"]
    n_true = seed_result["n_true"]
    assert sum(v[2] for v in st["origin"].values()) == n_true
    assert sum(v[2] for v in st["script"].values()) == n_true
    assert sum(st["fm_origin"].values()) == seed_result["systems"]["B5_hawiyya"]["fp"]
    found = sum(v[0] for v in st["origin"].values())
    assert found == seed_result["systems"]["B5_hawiyya"]["found"]


@pytest.mark.req("HW-L7-005")
def test_gold_set(ctx_xs) -> None:  # type: ignore[no-untyped-def]
    gold = load_gold()
    assert len(gold) >= 80
    assert {g["label"] for g in gold} == {"match", "non_match", "hard_negative"}
    assert all(g["reason"] for g in gold)
    rep = run_gold(load_model(), ctx_xs)
    assert rep["pairs"] == len(gold) and rep["author"].startswith("build_agent")


@pytest.mark.req("HW-L7-007")
def test_policies_are_pure(reg_xs) -> None:  # type: ignore[no-untyped-def]
    prep = prepare(reg_xs.records)
    u = B.build_universe(prep)
    before = [r.model_dump() for r in prep.records]
    a = B.b0_eid_exact(u, prep.records)
    b = B.b0_eid_exact(u, prep.records)
    c = B.b1_name_dob_exact(u, prep.records)
    assert np.array_equal(a, b)
    assert np.array_equal(c, B.b1_name_dob_exact(u, prep.records))
    assert [r.model_dump() for r in prep.records] == before


@pytest.mark.req("HW-L7-008")
def test_origin_label_is_not_a_model_input() -> None:
    model = load_model()
    reg = build_registry(5, "XS")  # a private copy, so relabelling cannot leak into other tests
    base = score_prepared(prepare(reg.records), model).log_odds
    for lab in reg.truth.labels.values():
        object.__setattr__(lab, "origin_group", "western")  # relabel every origin
    again = score_prepared(prepare(reg.records), model).log_odds
    assert np.array_equal(base, again)
    for pkg in ("normalise", "matching", "scoring", "decision"):
        for f in (ROOT / "src" / "hawiyya" / pkg).glob("*.py"):
            tree = ast.parse(f.read_text(encoding="utf-8"))
            names = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
            names |= {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
            assert "origin_group" not in names and "origin" not in names, f.name


@pytest.mark.req("HW-L7-006")
def test_sealed_seeds_only_through_the_sealed_command() -> None:
    with pytest.raises(PermissionError):
        run_suite("sealed")
    users = []
    for f in (ROOT / "src" / "hawiyya").rglob("*.py"):
        text = f.read_text(encoding="utf-8")
        if re.search(r"sealed_access\(\)", text):
            users.append(f.relative_to(ROOT).as_posix())
    assert sorted(users) == ["src/hawiyya/core/sealed.py", "src/hawiyya/lab/experiments.py"]


def test_seed_result_has_every_system(seed_result) -> None:  # type: ignore[no-untyped-def]
    assert set(seed_result["systems"]) == set(SYSTEMS)
    assert "sweep" in seed_result and "pc_lost_to_cap" in seed_result["blocking"]
