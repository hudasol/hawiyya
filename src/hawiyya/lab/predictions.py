"""Registered predictions: loading, mechanical judging against results, rendering."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from hawiyya.core.claims import json_pointer
from hawiyya.core.paths import RESULTS, SPEC

EXPERIMENTS_DIR = RESULTS / "experiments"
SPLITS = ("dev", "sealed")


@dataclass(frozen=True)
class Judgement:
    prediction_id: str
    split: str
    observed: Any
    hit: bool | None  # None when the result is not available


def load_predictions(path: Path | None = None) -> list[dict[str, Any]]:
    raw = json.loads((path or SPEC / "predictions.json").read_text(encoding="utf-8"))
    preds: list[dict[str, Any]] = raw["predictions"]
    return preds


def result_path(experiment: str, split: str) -> Path:
    return EXPERIMENTS_DIR / f"{experiment}_{split}.json"


def _field(d: Any, field: str) -> float:
    cur = d
    for part in field.split("/"):
        cur = cur[part]
    return float(cur)


def judge(pred: dict[str, Any], doc: dict[str, Any]) -> tuple[Any, bool]:
    op = pred["op"]
    this = json_pointer(doc, pred["pointer"])
    if op in ("argmin_eq", "range_le"):
        vals = {k: _field(v, pred["field"]) for k, v in this.items() if v is not None}
        if op == "argmin_eq":
            best = min(sorted(vals), key=lambda k: vals[k])
            return {"argmin": best, "values": vals}, best == pred["value"]
        spread = max(vals.values()) - min(vals.values())
        return {"range": round(spread, 6), "values": vals}, spread <= pred["value"]
    x = float(this)
    if op == "ge":
        return x, x >= pred["value"]
    if op == "le":
        return x, x <= pred["value"]
    if op == "between":
        lo, hi = pred["value"]
        return x, lo <= x <= hi
    if op in ("lt_ptr", "ge_ptr"):
        y = float(json_pointer(doc, pred["value"]))
        return {"this": x, "other": y}, (x < y) if op == "lt_ptr" else (x >= y)
    if op == "diff_ge":
        y = float(json_pointer(doc, pred["other"]))
        return {"this": x, "other": y}, (y - x) >= pred["value"]
    raise ValueError(f"unknown operator {op}")


def judge_all() -> list[Judgement]:
    out = []
    for p in load_predictions():
        for split in SPLITS:
            path = result_path(p["experiment"], split)
            if not path.exists():
                out.append(Judgement(p["id"], split, None, None))
                continue
            doc = json.loads(path.read_text(encoding="utf-8"))
            try:
                observed, hit = judge(p, doc)
            except (KeyError, IndexError, TypeError, ValueError):
                observed, hit = "not available", None
            out.append(Judgement(p["id"], split, observed, hit))
    return out


def _value_text(p: dict[str, Any]) -> str:
    v = p["value"]
    op = p["op"]
    if op == "between":
        return f"between {v[0]} and {v[1]}"
    if op == "ge":
        return f">= {v}"
    if op == "le":
        return f"<= {v}"
    if op == "lt_ptr":
        return f"< `{v}`"
    if op == "ge_ptr":
        return f">= `{v}`"
    if op == "diff_ge":
        return f"`{p['other']}` minus this >= {v}"
    if op == "argmin_eq":
        return f"lowest {p['field']} is `{v}`"
    if op == "range_le":
        return f"max minus min of {p['field']} <= {v}"
    return str(v)


def render_predictions() -> tuple[Path, str]:
    from hawiyya.core.paths import DOCS

    lines = [
        "# Predictions",
        "",
        "Registered before any experiment run (see `docs/PREREGISTRATION.md`). Rendered from",
        "`spec/predictions.json` by `hawiyya docs build`; do not edit by hand. Each prediction is",
        "judged mechanically in `docs/EVALUATION.md`.",
        "",
        "| ID | Experiment | Prediction | Result file pointer | Threshold |",
        "| --- | --- | --- | --- | --- |",
    ]
    for p in load_predictions():
        lines.append(f"| {p['id']} | {p['experiment']} | {p['text']} | `{p['pointer']}` | "
                     f"{_value_text(p)} |")  # fmt: skip
    lines.append("")
    return DOCS / "PREDICTIONS.md", "\n".join(lines)
