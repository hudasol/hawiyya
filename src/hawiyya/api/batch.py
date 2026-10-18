"""Batch views for the console: review queue, clusters, placeholders, threshold lab, audit.

Built once from the demonstration registry. Where a number uses ground truth it is labelled
"synthetic ground truth" in the payload.
"""

from __future__ import annotations

import json
import threading
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

import numpy as np

from hawiyya.contract.enums import ReviewState
from hawiyya.contract.models import Costs
from hawiyya.core.paths import RESULTS
from hawiyya.decision.batch import decide_batch
from hawiyya.decision.costs import DEFAULT_COSTS, LINK, REVIEW, decide_codes, thresholds
from hawiyya.decision.explain import explain
from hawiyya.decision.voi import next_best_questions
from hawiyya.normalise.identifiers import is_pattern_placeholder, normalise_value
from hawiyya.workflow.audit import verify
from hawiyya.workflow.batchrun import RUN_AT, BatchRun, run_batch
from hawiyya.workflow.export import STATEMENT, fhir_bundle, validate_bundle
from hawiyya.workflow.queue import ALLOWED

from .state import AppState, get_state

GUARD_FLOOR = 0.3  # guards are precomputed for pairs above this probability (threshold lab)
ACTIONS = {
    "assign": ReviewState.ASSIGNED,
    "request_merge": ReviewState.CONFIRMED_MERGE_REQUEST,
    "keep_apart": ReviewState.KEPT_APART,
    "cross_reference": ReviewState.CROSS_REFERENCED,
    "need_information": ReviewState.NEEDS_INFORMATION,
    "reopen": ReviewState.OPEN,
}


@dataclass
class BatchViews:
    run: BatchRun
    y: np.ndarray  # truth per candidate pair (synthetic ground truth, threshold lab only)
    guard_any: np.ndarray  # True when any guard fires for the pair (prob >= GUARD_FLOOR)
    cluster_ids: dict[str, list[str]]


_lock = threading.Lock()
_views: dict[str, BatchViews] = {}


def get_views() -> BatchViews:
    with _lock:
        if "v" not in _views:
            _views["v"] = _build(get_state())
        return _views["v"]


def _build(st: AppState) -> BatchViews:
    run = run_batch(list(st.registry.records), st.model, max_cases=300)
    prep, sc = run.prepared, run.scored
    ids = prep.record_ids()
    y = np.array([st.registry.truth.is_match(ids[int(i)], ids[int(j)]) for i, j in prep.pairs])
    # Guards for every pair that could become a LINK under some costs in the threshold lab.
    low = Costs(c_fm=1.0, c_md=1000.0, c_r=1000.0)
    probe = np.where(sc.prob >= GUARD_FLOOR, 0.9999, 0.0)
    bd = decide_batch(prep.pairs, prep.levels, sc.contrib, probe, prep.records, low)
    guard_any = bd.guard_bits != 0
    clusters = {f"K{n:04d}": members for n, members in enumerate(run.clusters.clusters)}
    return BatchViews(run, y, guard_any, clusters)


def _case_summary(c: Any) -> dict[str, Any]:
    return {"case_id": c.case_id, "record_a": c.record_a, "record_b": c.record_b,
            "state": c.state.value, "priority": c.priority,
            "probability": c.decision.evidence.pair.probability,
            "decision": c.decision.decision.value,
            "reason_codes": [r.value for r in c.decision.reason_codes],
            "created_at": c.created_at}  # fmt: skip


def review_queue(limit: int = 100) -> dict[str, Any]:
    v = get_views()
    q = v.run.queue
    cases = q.ordered()[:limit]
    return {"cases": [_case_summary(c) for c in cases], "workload": q.workload(),
            "total": len(q.cases)}  # fmt: skip


def review_case(case_id: str) -> dict[str, Any] | None:
    v = get_views()
    c = v.run.queue.cases.get(case_id)
    if c is None:
        return None
    st = get_state()
    recs = {r.record_id: r for r in v.run.prepared.records}
    d = c.decision
    qs = next_best_questions(d.evidence.pair.probability, st.model.params, d.costs)
    top = (qs[0].label_en, qs[0].label_ar) if qs else None
    return {
        **_case_summary(c),
        "records": [recs[c.record_a].model_dump(mode="json"), recs[c.record_b].model_dump(mode="json")],
        "score": d.evidence.pair.model_dump(mode="json"),
        "decision_detail": {**d.model_dump(mode="json", exclude={"evidence"}),
                            "explanation": explain(d, top)},
        "next_best_question": [vars(q) for q in qs],
        "expected_cost": c.expected_cost,
        "allowed_actions": [k for k, s in ACTIONS.items() if s in ALLOWED[c.state]],
        "history": [h.model_dump(mode="json") for h in c.history],
    }  # fmt: skip


def review_action(case_id: str, action: str) -> dict[str, Any]:
    v = get_views()
    to = ACTIONS[action]
    v.run.queue.transition(case_id, to, "sim_reviewer", RUN_AT)
    out = review_case(case_id)
    assert out is not None
    return out


def clusters(limit: int = 100) -> dict[str, Any]:
    v = get_views()
    conflicts = {x for a, b, _ in v.run.clusters.conflict_edges for x in (a, b)}
    rows: list[dict[str, Any]] = [
        {"cluster_id": cid, "size": len(m), "record_ids": m, "conflict": bool(set(m) & conflicts)}
        for cid, m in v.cluster_ids.items()
    ]
    rows.sort(key=lambda r: (-int(r["conflict"]), -r["size"], r["cluster_id"]))
    sizes = Counter(len(m) for m in v.cluster_ids.values())
    return {"clusters": rows[:limit], "total": len(rows),
            "conflict_edges": len(v.run.clusters.conflict_edges),
            "size_counts": {str(k): n for k, n in sorted(sizes.items())}}  # fmt: skip


def cluster_detail(cid: str) -> dict[str, Any] | None:
    v = get_views()
    members = v.cluster_ids.get(cid)
    if members is None:
        return None
    recs = {r.record_id: r for r in v.run.prepared.records}
    mset = set(members)
    edges = [{"a": a, "b": b, "probability": p} for a, b, p in v.run.clusters.accepted_edges
             if a in mset and b in mset]  # fmt: skip
    refused = [{"a": a, "b": b, "probability": p} for a, b, p in v.run.clusters.conflict_edges
               if a in mset or b in mset]  # fmt: skip
    bundle = fhir_bundle([recs[m] for m in members])
    validate_bundle(bundle)
    return {"cluster_id": cid, "records": [recs[m].model_dump(mode="json") for m in members],
            "edges": edges, "refused_edges": refused, "fhir_bundle": bundle,
            "statement": STATEMENT}  # fmt: skip


def placeholders() -> dict[str, Any]:
    st = get_state()
    reg = st.registry
    ctx = st.index.ctx
    groups: dict[str, list[str]] = defaultdict(list)
    for r in reg.records:
        v = normalise_value(r.id_value)
        if v:
            groups[v].append(r.record_id)
    rows: list[dict[str, Any]] = []
    for v, rids in groups.items():
        pattern = is_pattern_placeholder(v)
        learned = v in ctx.learned.identifiers
        if not (pattern or learned or len(rids) >= 5):
            continue
        persons = {reg.truth.person_of(r) for r in rids}
        n = len(rids)
        same = sum(1 for i in range(n) for j in range(i + 1, n)
                   if reg.truth.person_of(rids[i]) == reg.truth.person_of(rids[j]))  # fmt: skip
        rows.append({"value": v, "records": n, "pattern": pattern, "learned": learned,
                     "distinct_people_synthetic_truth": len(persons),
                     "naive_false_links_synthetic_truth": n * (n - 1) // 2 - same})  # fmt: skip
    rows.sort(key=lambda r: -r["records"])
    det = json.loads((RESULTS / "placeholder_detector.json").read_text(encoding="utf-8"))
    md = Counter(f"{r.dob.month:02d}-{r.dob.day:02d}" for r in ctx.records if r.dob)
    return {"identifiers": rows[:50], "learned_month_days": sorted(ctx.learned.month_days),
            "month_day_counts": {k: md[k] for k in sorted(ctx.learned.month_days)},
            "expected_per_day": round(sum(md.values()) / 365.25, 2),
            "detector_evaluation": det["per_seed"],
            "truth_label": "synthetic ground truth"}  # fmt: skip


def simulate_costs(c: Costs) -> dict[str, Any]:
    v = get_views()
    p = v.run.scored.prob
    codes = decide_codes(p, c)
    codes = np.where((codes == LINK) & v.guard_any, REVIEW, codes)
    n = len(v.run.prepared.records)
    y = v.y
    fm = int(((codes == LINK) & ~y).sum())
    tp = int(((codes == LINK) & y).sum())
    found = int(((codes >= REVIEW) & y).sum())
    t = thresholds(c)
    return {"costs": c.model_dump(), "thresholds": t.as_dict(),
            "false_merges_per_10k": round(fm / n * 1e4, 3),
            "missed_true_pairs_share": round(1 - found / max(1, int(y.sum())), 6),
            "auto_link_recall": round(tp / max(1, int(y.sum())), 6),
            "review_rate_per_1000": round(int((codes == REVIEW).sum()) / n * 1e3, 3),
            "truth_label": "synthetic ground truth (candidate pairs, guards, no clustering)"}  # fmt: skip


def threshold_curve() -> dict[str, Any]:
    v = get_views()
    p, y = v.run.scored.prob, v.y
    order = np.argsort(-p, kind="mergesort")
    ys = y[order]
    cov = []
    for c in (0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.5, 1.0):
        k = max(1, round(c * len(ys)))
        prec = float(ys[:k].mean())
        cov.append({"coverage": c, "precision": round(prec, 6),
                    "lo": round(_wilson_lo(int(ys[:k].sum()), k), 6), "n": k})  # fmt: skip
    hist, edges = np.histogram(p, bins=20, range=(0, 1))
    return {"risk_coverage": cov, "histogram": {"counts": hist.tolist(),
            "edges": [round(float(e), 3) for e in edges]},
            "default": simulate_costs(DEFAULT_COSTS),
            "truth_label": "synthetic ground truth"}  # fmt: skip


def _wilson_lo(k: int, n: int, z: float = 1.959964) -> float:
    p = k / n
    den = 1 + z * z / n
    return float((p + z * z / (2 * n) - z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / den)


def audit(limit: int = 200) -> dict[str, Any]:
    v = get_views()
    ev = v.run.audit.events
    return {"events": [e.model_dump(mode="json") for e in ev[-limit:]], "total": len(ev),
            "chain_ok": verify(ev) is None, "head": v.run.audit.head}  # fmt: skip
