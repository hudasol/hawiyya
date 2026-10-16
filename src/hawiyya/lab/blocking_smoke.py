"""Development smoke check of blocking (one development seed). Not an experiment result.

The preregistered experiment E1 runs later over many seeds; this file exists so the P3 gate
has evidence that blocking works, and it is kept under ``results/dev/``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from hawiyya.core.paths import RESULTS
from hawiyya.matching.blocking import DEFAULT_CAP, block, pair_completeness
from hawiyya.normalise.record import normalise_registry
from hawiyya.registry.build import build_registry


def run(seed: int = 7, tier: str = "S") -> dict[str, Any]:
    reg = build_registry(seed, tier)
    ctx = normalise_registry(reg.records)
    idx = {r.record_id: i for i, r in enumerate(ctx.records)}
    tp = np.array(sorted((min(idx[a], idx[b]), max(idx[a], idx[b]))
                         for a, b in reg.truth.true_pairs()))  # fmt: skip
    n = len(ctx.records)
    capped = block(ctx.records)
    uncapped = block(ctx.records, cap=10**9)
    pc_cap = pair_completeness(capped.pairs, tp, n)
    pc_full = pair_completeness(uncapped.pairs, tp, n)
    return {
        "note": "Development smoke check on one development seed; not an experiment result.",
        "seed": seed, "tier": tier, "generator": "G1", "n_records": n,
        "true_pairs": len(tp),
        "candidate_pairs": len(capped.pairs),
        "pairs_per_record": round(capped.pairs_per_record, 3),
        "reduction_ratio": round(capped.reduction_ratio, 6),
        "pair_completeness": round(pc_cap, 4),
        "pair_completeness_without_cap": round(pc_full, 4),
        "pair_completeness_lost_to_cap": round(pc_full - pc_cap, 4),
        "cap": DEFAULT_CAP, "capped_blocks": capped.capped_blocks,
        "largest_block": capped.largest_block,
        "pairs_per_pass": dict(sorted(capped.per_pass.items())),
    }  # fmt: skip


def write(path: Path | None = None) -> dict[str, Any]:
    rep = run()
    out = path or RESULTS / "dev" / "blocking_smoke.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rep, indent=2) + "\n", encoding="utf-8", newline="\n")
    return rep
