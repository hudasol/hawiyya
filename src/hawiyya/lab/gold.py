"""Gold set smoke test (author: build_agent, not independent). Never a headline claim.

84 hand authored pairs labelled match, non match or hard negative, each with a one line
reason. They were written with knowledge of the matcher's design, so they are a reading aid and
a smoke test only.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from hawiyya.contract.models import Record
from hawiyya.core.paths import DATA, RESULTS
from hawiyya.decision.costs import DEFAULT_COSTS
from hawiyya.decision.engine import decide
from hawiyya.matching.compare import features
from hawiyya.normalise.record import apply_learned, normalise_record
from hawiyya.scoring.scorer import Model, Scorer

GOLD = DATA / "gold" / "gold_pairs.jsonl"
KEYS = {"n": "name_latin", "ar": "name_ar", "d": "dob", "s": "sex", "i": "id_value",
        "k": "id_kind", "c": "id_capture", "p": "phone"}  # fmt: skip


def load_gold(path: Path = GOLD) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def to_record(d: dict[str, Any], rid: str) -> Record:
    fields = {KEYS[k]: v for k, v in d.items()}
    if fields.get("dob"):
        fields["dob_precision"] = "day"
    return Record.model_validate({"record_id": rid, "facility_id": "GOLD",
                                  "registered_on": "2026-01-01", **fields})  # fmt: skip


def run_gold(model: Model, scorer_ctx: Any) -> dict[str, Any]:
    rows = []
    table: Counter[tuple[str, str]] = Counter()
    for g in load_gold():
        a, b = to_record(g["a"], g["id"] + "A"), to_record(g["b"], g["id"] + "B")
        fa = features(apply_learned(normalise_record(a), scorer_ctx.learned))
        fb = features(apply_learned(normalise_record(b), scorer_ctx.learned))
        ps = Scorer(model, scorer_ctx.tf).pair_score(fa, fb)
        d = decide(ps, a, b, DEFAULT_COSTS)
        table[(g["label"], d.decision.value)] += 1
        rows.append({"id": g["id"], "label": g["label"], "decision": d.decision.value,
                     "probability": round(ps.probability, 6),
                     "guards": [x.value for x in d.guards_fired]})  # fmt: skip
    false_links = [r["id"] for r in rows if r["label"] != "match" and r["decision"] == "LINK"]
    return {
        "author": "build_agent, not independent",
        "note": "Smoke test and reading aid only; never a headline claim.",
        "pairs": len(rows),
        "by_label_and_decision": {f"{k[0]}|{k[1]}": v for k, v in sorted(table.items())},
        "non_matches_linked": false_links,
        "rows": rows,
    }


def write_gold_report(model: Model, scorer_ctx: Any) -> dict[str, Any]:
    rep = run_gold(model, scorer_ctx)
    out = RESULTS / "gold_smoke.json"
    out.write_text(json.dumps(rep, indent=1) + "\n", encoding="utf-8", newline="\n")
    return rep
