"""Evaluate the placeholder detectors against the injected truth (development seeds only)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from hawiyya.core.paths import RESULTS
from hawiyya.normalise.identifiers import is_pattern_placeholder, normalise_value
from hawiyya.normalise.record import normalise_registry
from hawiyya.registry.build import build_registry


def _prf(pred: set[str], truth: set[str]) -> dict[str, Any]:
    tp = len(pred & truth)
    precision = tp / len(pred) if pred else 1.0
    recall = tp / len(truth) if truth else 1.0
    return {"predicted": len(pred), "true": len(truth), "true_positives": tp,
            "precision": round(precision, 4), "recall": round(recall, 4)}  # fmt: skip


def evaluate_seed(seed: int, tier: str = "S") -> dict[str, Any]:
    reg = build_registry(seed, tier)
    ctx = normalise_registry(reg.records)
    truth_values: set[str] = set()
    for r in reg.records:
        if reg.truth.is_placeholder(r.record_id):
            v = normalise_value(r.id_value)
            if v:
                truth_values.add(v)
    all_values = {v for r in reg.records if (v := normalise_value(r.id_value))}
    pattern = {v for v in all_values if is_pattern_placeholder(v)}
    flagged_on_form = {normalise_value(r.id_value) or "" for r in reg.records
                       if r.id_kind is not None and r.id_kind.value == "PLACEHOLDER"}  # fmt: skip
    learned = set(ctx.learned.identifiers)
    union = pattern | learned | flagged_on_form
    ph_records = sum(reg.truth.is_placeholder(r.record_id) for r in reg.records)
    caught = sum(1 for r in ctx.records if r.ident.placeholder
                 and reg.truth.is_placeholder(r.record_id))  # fmt: skip
    flagged = sum(1 for r in ctx.records if r.ident.placeholder)
    return {
        "seed": seed,
        "value_level": {
            "pattern": _prf(pattern, truth_values),
            "learned": _prf(learned, truth_values),
            "learned_minus_pattern": _prf(learned - pattern, truth_values - pattern),
            "combined": _prf(union, truth_values),
        },
        "record_level": {
            "placeholder_records": ph_records,
            "flagged_records": flagged,
            "recall": round(caught / ph_records, 4) if ph_records else 1.0,
            "precision": round(caught / flagged, 4) if flagged else 1.0,
        },
        "learned_month_days": sorted(ctx.learned.month_days),
    }


def write_report(seeds: tuple[int, ...] = (1, 2, 3), path: Path | None = None) -> dict[str, Any]:
    per_seed = [evaluate_seed(s) for s in seeds]
    report = {
        "description": "Placeholder detectors evaluated against the identifier values that the "
        "generator injected as placeholders (synthetic ground truth), on development seeds.",
        "generator": "G1",
        "tier": "S",
        "seeds": list(seeds),
        "per_seed": per_seed,
    }
    out = path or RESULTS / "placeholder_detector.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    return report
