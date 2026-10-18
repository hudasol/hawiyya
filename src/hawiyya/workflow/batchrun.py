"""Batch deduplication run: score every candidate pair, decide, cluster, open review cases,
and record the run in the audit log."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np

from hawiyya.contract.enums import AuditKind, ReasonCode
from hawiyya.contract.models import Costs, Record
from hawiyya.core.determinism import stable_hash
from hawiyya.decision.batch import BatchDecisions, decide_batch
from hawiyya.decision.cluster import CONTRADICTION_LOG_ODDS, ClusterResult, cluster
from hawiyya.decision.costs import DEFAULT_COSTS, LINK, REVIEW
from hawiyya.decision.engine import decide
from hawiyya.scoring.pipeline import Prepared, Scored, prepare, score_prepared
from hawiyya.scoring.scorer import Model, Scorer
from hawiyya.workflow.audit import AuditLog
from hawiyya.workflow.queue import ReviewQueue, new_case

RUN_AT = "2026-10-01T00:00:00Z"  # fixed timestamp keeps batch outputs deterministic
AS_OF = date(2026, 10, 1)


@dataclass
class BatchRun:
    prepared: Prepared
    scored: Scored
    decisions: BatchDecisions
    clusters: ClusterResult
    queue: ReviewQueue
    audit: AuditLog

    def ids(self) -> list[str]:
        return self.prepared.record_ids()

    def final_codes(self) -> np.ndarray:
        """Decision codes after clustering: refused LINK edges become REVIEW."""
        codes = self.decisions.codes.copy()
        ids = self.ids()
        refused = {(a, b) for a, b, _ in self.clusters.conflict_edges}
        for k in np.flatnonzero(codes == LINK):
            i, j = map(int, self.prepared.pairs[k])
            a, b = sorted((ids[i], ids[j]))
            if (a, b) in refused:
                codes[k] = REVIEW
        return codes


def run_batch(records: list[Record], model: Model, costs: Costs = DEFAULT_COSTS,
              max_cases: int = 400, audit: AuditLog | None = None) -> BatchRun:
    prep = prepare(records)
    sc = score_prepared(prep, model)
    bd = decide_batch(prep.pairs, prep.levels, sc.contrib, sc.prob, prep.records, costs)
    ids = prep.record_ids()
    links = [(ids[int(i)], ids[int(j)], float(sc.prob[k]))
             for k, (i, j) in enumerate(prep.pairs) if bd.codes[k] == LINK]  # fmt: skip
    contra = [(ids[int(i)], ids[int(j)])
              for k, (i, j) in enumerate(prep.pairs) if sc.log_odds[k] < CONTRADICTION_LOG_ODDS
              or int(bd.guard_bits[k]) != 0]  # fmt: skip
    cl = cluster(links, contra)
    log = audit or AuditLog()
    run_hash = stable_hash({"records": len(records), "model": model.version,
                            "costs": costs.model_dump(mode="json")}, length=24)  # fmt: skip
    queue = ReviewQueue(audit=log)
    refused = {(a, b) for a, b, _ in cl.conflict_edges}
    review_idx = [k for k in np.flatnonzero(bd.codes == REVIEW)]
    for k in np.flatnonzero(bd.codes == LINK):
        i, j = map(int, prep.pairs[k])
        if tuple(sorted((ids[i], ids[j]))) in refused:
            review_idx.append(k)
    review_idx.sort(key=lambda k: -min(costs.c_fm * (1 - sc.prob[k]), costs.c_md * sc.prob[k]))
    scorer = Scorer(model, prep.ctx.tf)
    for k in review_idx[:max_cases]:
        i, j = map(int, prep.pairs[k])
        ps = scorer.pair_score(prep.feats[i], prep.feats[j])
        d = decide(ps, prep.records[i], prep.records[j], costs)
        if tuple(sorted((ids[i], ids[j]))) in refused:
            d = d.model_copy(update={"reason_codes": [*d.reason_codes, ReasonCode.CLUSTER_CONFLICT]})
        created = max(prep.records[i].registered_on, prep.records[j].registered_on)
        case = new_case(d, f"{created}T00:00:00Z", AS_OF)
        queue.add(case)
        log.append(AuditKind.DECISION, [case.case_id, case.record_a, case.record_b],
                   d.inputs_hash, RUN_AT, {"decision": d.decision.value})  # fmt: skip
    counts = {name: int((bd.codes == code).sum()) for name, code in
              (("link", LINK), ("review", REVIEW), ("keep_apart", 0))}  # fmt: skip
    log.append(AuditKind.SCORE, ["batch"], run_hash, RUN_AT,
               {"pairs": len(prep.pairs), **counts, "clusters": len(cl.clusters),
                "cluster_conflicts": len(cl.conflict_edges)})  # fmt: skip
    return BatchRun(prep, sc, bd, cl, queue, log)
