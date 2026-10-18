"""L6 workflow tests: review queue, audit chain, exports, simulated reviewer, batch run."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from hawiyya.contract.enums import AuditKind, ReviewState
from hawiyya.lab.train import load_model
from hawiyya.normalise.identifiers import is_pattern_placeholder
from hawiyya.workflow.audit import AuditLog, verify, verify_file
from hawiyya.workflow.batchrun import RUN_AT, run_batch
from hawiyya.workflow.export import (
    STATEMENT,
    fhir_bundle,
    one_page_summary,
    review_csv,
    validate_bundle,
)
from hawiyya.workflow.queue import ALLOWED, TERMINAL, IllegalTransition, priority
from hawiyya.workflow.reviewer import ReviewerModel, simulate


@pytest.fixture(scope="module")
def run(reg_xs, tmp_path_factory):  # type: ignore[no-untyped-def]
    path = tmp_path_factory.mktemp("audit") / "audit.jsonl"
    return run_batch(list(reg_xs.records), load_model(), audit=AuditLog(path)), path


@pytest.mark.req("HW-L6-001")
def test_queue_transitions_follow_allowed_edges(run) -> None:  # type: ignore[no-untyped-def]
    br, _ = run
    q = br.queue
    assert q.cases, "a batch run should open review cases"
    cid = q.ordered()[0].case_id
    with pytest.raises(IllegalTransition):
        q.transition(cid, ReviewState.CONFIRMED_MERGE_REQUEST, "sim_reviewer", RUN_AT)
    q.transition(cid, ReviewState.ASSIGNED, "sim_reviewer", RUN_AT)
    q.transition(cid, ReviewState.KEPT_APART, "sim_reviewer", RUN_AT)
    with pytest.raises(IllegalTransition):
        q.transition(cid, ReviewState.OPEN, "sim_reviewer", RUN_AT)
    assert q.cases[cid].state == ReviewState.KEPT_APART
    assert len(q.cases[cid].history) == 2
    for s in TERMINAL:
        assert not ALLOWED[s]


@pytest.mark.req("HW-L6-002")
def test_audit_chain_verifies_and_detects_tampering(run, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    br, path = run
    assert verify(br.audit.events) is None
    assert verify_file(path) is None
    lines = path.read_text(encoding="utf-8").splitlines()
    doc = json.loads(lines[1])
    doc["detail"]["decision"] = "LINK"
    lines[1] = json.dumps(doc)
    bad = tmp_path / "tampered.jsonl"
    bad.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert verify_file(bad) == 1
    dropped = tmp_path / "dropped.jsonl"
    dropped.write_text("\n".join(lines[:1] + lines[2:]) + "\n", encoding="utf-8")
    assert verify_file(dropped) is not None


@pytest.mark.req("HW-L6-003")
def test_audit_log_has_no_names_or_identifiers(run, reg_xs) -> None:  # type: ignore[no-untyped-def]
    _, path = run
    text = path.read_text(encoding="utf-8")
    secrets = set()
    for r in reg_xs.records:
        for v in (r.name_latin, r.name_ar, r.id_value, r.phone):
            # Placeholder values (all zeros and so on) identify nobody; all zeros also occurs
            # inside the chain's genesis hash.
            if v and len(v) >= 6 and not is_pattern_placeholder(v):
                secrets.add(v)
    assert not [s for s in secrets if s in text]
    with pytest.raises(ValueError):
        AuditLog().append(AuditKind.EXPORT, ["Mohammed Ali"], "abcdef12", RUN_AT)
    with pytest.raises(ValueError):
        AuditLog().append(AuditKind.EXPORT, ["R000001"], "abcdef12", RUN_AT,
                          {"id": "784199012345671"})


@pytest.mark.req("HW-L6-005")
def test_fhir_bundle_validates_and_carries_statement(run) -> None:  # type: ignore[no-untyped-def]
    br, _ = run
    recs = {r.record_id: r for r in br.prepared.records}
    cluster = br.clusters.clusters[0]
    bundle = fhir_bundle([recs[i] for i in cluster])
    validate_bundle(bundle)
    assert bundle["extension"][0]["valueString"] == STATEMENT
    kinds = [lk["type"] for e in bundle["entry"] for lk in e["resource"].get("link", [])]
    assert "replaces" in kinds and "replaced-by" in kinds
    xref = fhir_bundle([recs[cluster[0]], recs[cluster[1]]], cross_reference=True)
    validate_bundle(xref)
    assert {lk["type"] for e in xref["entry"] for lk in e["resource"]["link"]} == {"seealso"}
    broken = json.loads(json.dumps(bundle))
    broken["entry"][0]["resource"]["link"] = [{"other": {"reference": "x"}, "type": "merge"}]
    with pytest.raises(jsonschema.ValidationError):
        validate_bundle(broken)


@pytest.mark.req("HW-L6-006")
def test_csv_and_summary_carry_statement(run) -> None:  # type: ignore[no-untyped-def]
    br, _ = run
    text = review_csv(br.queue.ordered())
    assert text.startswith("# " + STATEMENT)
    assert "case_id,record_a,record_b" in text
    summary = one_page_summary({"review_cases": len(br.queue.cases)})
    assert STATEMENT in summary


@pytest.mark.req("HW-L6-007")
def test_simulated_reviewer(run, reg_xs) -> None:  # type: ignore[no-untyped-def]
    br, _ = run
    pairs = [(c.record_a, c.record_b) for c in br.queue.ordered()]
    perfect = simulate(pairs, reg_xs.truth.is_match, ReviewerModel(1.0, 3.0), seed=1)
    assert perfect.false_merges == 0 and perfect.missed_duplicates == 0
    assert perfect.minutes == pytest.approx(3.0 * len(pairs))
    sloppy = simulate(pairs, reg_xs.truth.is_match, ReviewerModel(0.5, 3.0), seed=1)
    assert sloppy.false_merges + sloppy.missed_duplicates > 0


@pytest.mark.req("HW-L6-008")
def test_priority_by_expected_cost_and_age(run) -> None:  # type: ignore[no-untyped-def]
    br, _ = run
    from hawiyya.decision.costs import DEFAULT_COSTS as C

    assert priority(0.5, C, 0) > priority(0.99, C, 0)
    assert priority(0.5, C, 14) > priority(0.5, C, 0)
    pr = [c.priority for c in br.queue.ordered()]
    assert pr == sorted(pr, reverse=True)


def test_batch_run_clusters_and_audit(run) -> None:  # type: ignore[no-untyped-def]
    br, _ = run
    assert br.clusters.clusters
    assert any(e.kind == AuditKind.SCORE for e in br.audit.events)
    for a, b, _p in br.clusters.conflict_edges:
        assert not any({a, b} <= set(c) for c in br.clusters.clusters)
