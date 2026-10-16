"""L1 registry tests."""

from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from itertools import combinations
from pathlib import Path

import pytest

from hawiyya.contract.enums import IdCapture, IdKind
from hawiyya.contract.models import TRUTH_FIELDS, Record
from hawiyya.core.errors import SchemaDriftError, SealedSeedError
from hawiyya.core.paths import DOCS, RESULTS, ROOT
from hawiyya.lab.lexicon_report import build_report
from hawiyya.registry import manifest, source
from hawiyya.registry.build import build_registry, registry_bytes
from hawiyya.registry.facilities import FACILITIES
from hawiyya.registry.lexicon import NameEntry, default_lexicon, load_denylist, load_lexicon


@pytest.mark.req("HW-L1-001", "HW-X-009")
def test_same_seed_gives_identical_registry() -> None:
    a = build_registry(11, "XS")
    b = build_registry(11, "XS")
    c = build_registry(12, "XS")
    assert registry_bytes(a) == registry_bytes(b)
    assert a.digest() == b.digest()
    assert registry_bytes(a) != registry_bytes(c)


@pytest.mark.req("HW-L1-002")
def test_every_duplicate_has_ground_truth(reg_s) -> None:  # type: ignore[no-untyped-def]
    ids = {r.record_id for r in reg_s.records}
    assert set(reg_s.truth.labels) == ids
    by_person = defaultdict(list)
    for rid, lab in reg_s.truth.labels.items():
        assert lab.person_id in reg_s.truth.people.by_id
        by_person[lab.person_id].append(rid)
    expected = sum(len(v) * (len(v) - 1) // 2 for v in by_person.values())
    pairs = reg_s.truth.true_pairs()
    assert len(pairs) == expected > 0
    for a, b in list(pairs)[:500]:
        assert reg_s.truth.is_match(a, b)


@pytest.mark.req("HW-L1-003")
def test_registration_view_has_no_truth_field(reg_s) -> None:  # type: ignore[no-untyped-def]
    assert not set(Record.model_fields) & TRUTH_FIELDS
    for r in reg_s.records[:200]:
        assert not set(r.model_dump()) & TRUTH_FIELDS


@pytest.mark.req("HW-L1-004")
def test_denylist_is_enforced(reg_s, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    deny = load_denylist()
    lex = default_lexicon()
    assert not any(deny.family_denied(f) for f in lex.family)
    for p in reg_s.truth.people.persons:
        assert p.given is not None and p.family is not None
        assert not deny.combination_denied(p.given, p.family)
    bad = json.loads((ROOT / "data/lexicon/names.json").read_text(encoding="utf-8"))
    bad["family"].append({"ar": "x", "latin": ["Al Maktoum"], "origins": "G", "tier": 1})
    path = tmp_path / "names.json"
    path.write_text(json.dumps(bad, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError):
        load_lexicon(path)
    imran = NameEntry("x", ("Imran",), (), 1, "M")
    khan = NameEntry("y", ("Khan",), (), 1)
    assert deny.combination_denied(imran, khan)


def _write_chunk(base: Path, header: list[str], row: list[str]) -> None:
    d = base / "chunk00" / "csv"
    d.mkdir(parents=True)
    with (d / "patients.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerow(row)
    with (d / "encounters.csv").open("w", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerow(["PATIENT"])


@pytest.mark.req("HW-L1-005")
def test_adapter_fails_loudly_on_schema_drift(tmp_path: Path) -> None:
    _write_chunk(tmp_path / "a", ["Id", "BIRTHDATE", "DEATHDATE", "SEX", "COUNTY"],
                 ["x", "2000-01-01", "", "M", "C"])
    with pytest.raises(SchemaDriftError, match=r"patients\.csv.*'GENDER'"):
        source.read_synthea_chunks(tmp_path / "a")
    _write_chunk(tmp_path / "b", ["Id", "BIRTHDATE", "DEATHDATE", "GENDER", "COUNTY"],
                 ["x", "01/01/2000", "", "M", "C"])
    with pytest.raises(SchemaDriftError, match="BIRTHDATE"):
        source.read_synthea_chunks(tmp_path / "b")
    _write_chunk(tmp_path / "c", ["Id", "BIRTHDATE", "DEATHDATE", "GENDER", "COUNTY"],
                 ["x", "2000-01-01", "", "X", "C"])
    with pytest.raises(SchemaDriftError, match="GENDER"):
        source.read_synthea_chunks(tmp_path / "c")


@pytest.mark.req("HW-L1-006")
def test_manifest_hashes_verify() -> None:
    assert manifest.verify_manifest() == []
    m = manifest.load_manifest()
    assert set(m["files_sha256"]) == set(manifest.HASHED_FILES)


@pytest.mark.req("HW-L1-007")
def test_data_source_matches_docs() -> None:
    m = manifest.load_manifest()
    label = m["data_source_label"]
    for doc in (ROOT / "README.md", DOCS / "DATA_STATEMENT.md"):
        text = doc.read_text(encoding="utf-8")
        assert f"Data source: {label}" in text, doc.name
        if m["data_source"] == "native":
            assert "Synthea" not in text


@pytest.mark.req("HW-L1-008")
def test_hard_negatives_are_present(reg_s) -> None:  # type: ignore[no-untyped-def]
    recs = reg_s.view.by_id()
    truth = reg_s.truth
    groups: dict[str, list[str]] = defaultdict(list)
    for r in reg_s.records:
        lab = truth.labels[r.record_id]
        p = truth.people.get(lab.person_id)
        groups["clan:" + p.clan_id].append(r.record_id)
        groups["fam:" + p.family_id].append(r.record_id)
        groups[f"dob:{p.birth_date}:{p.sex}"].append(r.record_id)
        if r.id_kind == IdKind.PLACEHOLDER:
            groups["ph:" + str(r.id_value)].append(r.record_id)
    seen = set()
    for ids in groups.values():
        for a, b in combinations(ids[:60], 2):
            seen.add(truth.category(recs[a], recs[b]))
    needed = {"twin", "sibling", "father_son_same_name", "parent_child", "cousin",
              "same_dob_sex", "newborn_mother_shared_id", "shared_placeholder"}
    assert needed <= seen, needed - seen


@pytest.mark.req("HW-L1-009")
def test_six_facilities_with_styles(reg_s) -> None:  # type: ignore[no-untyped-def]
    assert len(FACILITIES) >= 6
    assert len({f.style for f in FACILITIES}) == len(FACILITIES)
    used = {r.facility_id for r in reg_s.records}
    assert used == {f.facility_id for f in FACILITIES}


@pytest.mark.req("HW-L1-010")
def test_lexicon_report_is_written_and_fresh() -> None:
    path = RESULTS / "lexicon_report.json"
    on_disk = json.loads(path.read_text(encoding="utf-8"))
    assert on_disk == build_report(default_lexicon())
    assert 0.0 <= on_disk["skeleton"]["collision_rate"] <= 1.0


@pytest.mark.req("HW-L1-011")
def test_identifier_format_and_placeholders(reg_s) -> None:  # type: ignore[no-untyped-def]
    eid = re.compile(r"^784\d{12}$")
    n_ph = 0
    for r in reg_s.records:
        lab = reg_s.truth.labels[r.record_id]
        p = reg_s.truth.people.get(lab.person_id)
        if r.id_kind == IdKind.EID and r.id_capture == IdCapture.READER:
            assert eid.match(str(r.id_value))
            assert r.id_value == p.eid
            assert str(r.id_value)[3:7] == f"{p.birth_date.year:04d}"
        if r.id_kind == IdKind.PLACEHOLDER:
            n_ph += 1
    assert n_ph > 0
    assert any(r.id_value == "1" * 15 for r in reg_s.records)


@pytest.mark.req("HW-L1-012")
def test_tier_s_size(reg_s) -> None:  # type: ignore[no-untyped-def]
    assert reg_s.meta["n_persons"] == 5000
    assert 10000 <= reg_s.meta["n_records"] <= 14000


@pytest.mark.slow
@pytest.mark.req("HW-L1-012")
def test_tier_m_size() -> None:
    reg = build_registry(4, "M")
    assert reg.meta["n_persons"] == 20000
    assert 40000 <= reg.meta["n_records"] <= 56000


@pytest.mark.req("HW-L1-014")
def test_optional_reweighting() -> None:
    pool = source.read_sample()
    out = source.reweight(pool, 1000, seed=1, male_share=0.7)
    assert len(out) == 1000
    assert sum(p.sex == "M" for p in out) == 700


def test_native_source_has_same_schema() -> None:
    people = source.native_population(200, seed=1)
    assert len(people) == 200
    assert people == source.native_population(200, seed=1)
    reg = build_registry(2, "XS", source="native")
    assert reg.meta["data_source"] == "native"


def test_sealed_seed_cannot_be_built() -> None:
    with pytest.raises(SealedSeedError):
        build_registry(1001, "XS")
