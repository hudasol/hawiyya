"""Render evaluation tables from results/experiments/*.json into docs/EVALUATION.md blocks.

Every number in these blocks is copied from a results file by this code, so the document
cannot disagree with its sources (a freshness test re renders and compares).
"""

from __future__ import annotations

import json
from typing import Any

from hawiyya.core.paths import RESULTS
from hawiyya.lab.predictions import EXPERIMENTS_DIR, judge_all, load_predictions

SYSTEM_LABELS = {
    "B0_eid_exact": "B0 identifier exact",
    "B1_name_dob_exact": "B1 name and date exact",
    "B2_fuzzy_raw": "B2 fuzzy raw names",
    "B3_latin_only": "B3 Hawiyya, Latin only",
    "B4_forced": "B4 Hawiyya, forced (no review)",
    "B5_hawiyya": "B5 Hawiyya (product)",
    "B6_gbm": "B6 supervised reference",
}
METRICS = (("link_precision", "LINK precision", 4), ("link_recall", "LINK recall", 4),
           ("link_f1", "LINK F1", 4), ("false_merges_per_10k", "False merges per 10k", 1),
           ("found_recall", "Found recall", 4), ("review_rate", "Reviews per 1k", 1),
           ("bcubed_precision", "B cubed precision", 4), ("bcubed_recall", "B cubed recall", 4))  # fmt: skip


def _load(name: str) -> dict[str, Any] | None:
    p = EXPERIMENTS_DIR / f"{name}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def _ci(d: dict[str, Any] | None, digits: int) -> str:
    if not d or d.get("mean") is None:
        return "n/a"
    return f"{d['mean']:.{digits}f} [{d['lo']:.{digits}f}, {d['hi']:.{digits}f}]"


def _rate(d: dict[str, Any] | None) -> str:
    if not d or d.get("rate") is None:
        return "n/a"
    return f"{d['rate']:.4f} [{d['lo']:.4f}, {d['hi']:.4f}] (n={d['n']})"


def _fmt_obs(obs: Any) -> str:
    if obs is None:
        return "not run"
    if isinstance(obs, float):
        return f"{obs:.6g}"
    if isinstance(obs, dict):
        if "argmin" in obs:
            return f"lowest: {obs['argmin']}"
        if "range" in obs:
            return f"range {obs['range']:.4f}"
        if "this" in obs:
            return f"{obs['this']:.6g} vs {obs['other']:.6g}"
    return str(obs)


def predictions_block() -> str:
    judged = judge_all()
    by = {(j.prediction_id, j.split): j for j in judged}
    lines = ["| ID | Prediction | Development | Result | Sealed | Result |",
             "| --- | --- | --- | --- | --- | --- |"]
    hits = {"dev": [0, 0], "sealed": [0, 0]}
    for p in load_predictions():
        cells = []
        for split in ("dev", "sealed"):
            j = by[(p["id"], split)]
            verdict = "not run" if j.hit is None else ("HIT" if j.hit else "MISS")
            if j.hit is not None:
                hits[split][0] += int(j.hit)
                hits[split][1] += 1
            cells += [_fmt_obs(j.observed), verdict]
        lines.append(f"| {p['id']} | {p['text']} | " + " | ".join(cells) + " |")
    lines.append("")
    for split, (h, n) in hits.items():
        lines.append(f"- {split}: {h} hits out of {n} judged predictions.")
    return "\n".join(lines)


def systems_table(doc: dict[str, Any] | None, systems: dict[str, Any] | None = None) -> str:
    if doc is None:
        return "Not run yet."
    sys_ = systems if systems is not None else doc["systems"]
    head = "| System | " + " | ".join(m[1] for m in METRICS) + " |"
    lines = [head, "| --- |" + " --- |" * len(METRICS)]
    for key, vals in sys_.items():
        cells = [_ci(vals.get(m[0]), m[2]) for m in METRICS]
        lines.append(f"| {SYSTEM_LABELS.get(key, key)} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def baseline_wins(doc: dict[str, Any] | None) -> list[str]:
    """Every metric where a baseline's mean is better than the product's."""
    if doc is None:
        return []
    prod = doc["systems"].get("B5_hawiyya")
    if prod is None:
        return []
    better_high = ("link_precision", "link_recall", "link_f1", "found_recall",
                   "bcubed_precision", "bcubed_recall")  # fmt: skip
    out = []
    for key, vals in doc["systems"].items():
        if key == "B5_hawiyya":
            continue
        for m, label, digits in METRICS:
            a, b = vals.get(m, {}).get("mean"), prod.get(m, {}).get("mean")
            if a is None or b is None:
                continue
            # Lower is better for false merges and for review workload.
            wins = a > b if m in better_high else a < b
            if wins:
                out.append(f"{SYSTEM_LABELS.get(key, key)} beats the product on {label} "
                           f"({a:.{digits}f} against {b:.{digits}f}).")  # fmt: skip
    return out


def experiments_block(split: str) -> str:
    out: list[str] = []
    e1 = _load(f"E1_{split}")
    if e1 is None:
        return f"The {split} experiments have not been run yet."
    out.append(f"### E1 blocking ({split})\n")
    out.append("| Generator | Pair completeness | Lost to the cap | Reduction ratio | Pairs per record |")
    out.append("| --- | --- | --- | --- | --- |")
    for g, v in e1["generators"].items():
        out.append(f"| {g} | {_ci(v.get('pair_completeness'), 4)} | {_ci(v.get('pc_lost_to_cap'), 4)} "
                   f"| {_ci(v.get('reduction_ratio'), 6)} | {_ci(v.get('pairs_per_record'), 2)} |")  # fmt: skip
    e2 = _load(f"E2_{split}")
    out.append(f"\n### E2 systems on G1 ({split}; mean [95% interval] over {len(e2['seeds']['g1']) if e2 else 0} seeds)\n")
    out.append(systems_table(e2))
    wins = baseline_wins(e2)
    out.append("\nWhere a baseline beats the product:\n")
    out += [f"- {w}" for w in wins] or ["- none"]
    e3 = _load(f"E3_{split}")
    if e3:
        out.append(f"\n### E3 calibration and abstention ({split})\n")
        out.append(f"- Expected calibration error: {_ci(e3['ece'], 4)}")
        out.append(f"- Precision of automatic LINKs: {_ci(e3['auto_link_precision'], 4)}")
        out.append(f"- Share of candidate pairs sent to review: {_ci(e3['review_share'], 4)}")
        est = e3["estimation"]
        out.append(f"- Estimation (fitting seeds): lambda plain EM {est['plain_em_lambda']}, anchored "
                   f"{est['anchored_lambda']}, labels {est['label_lambda']}; average precision plain EM "
                   f"{est['plain_em_average_precision']}, anchored {est['anchored_average_precision']}, "
                   f"labels {est['label_average_precision']}.")  # fmt: skip
        out.append("\n| Probability bin | Pairs | Mean predicted | Observed |")
        out.append("| --- | --- | --- | --- |")
        for b in e3["reliability"]:
            out.append(f"| {b['bin']:.1f} | {b['n']} | {b['mean_predicted']} | {b['observed']} |")
        out.append("\n| Coverage (share of candidates, highest probability first) | Precision |")
        out.append("| --- | --- |")
        for pt in e3["risk_coverage"]:
            out.append(f"| {pt['coverage']} | {pt['precision']:.4f} |")
    e4 = _load(f"E4_{split}")
    if e4:
        out.append(f"\n### E4 found recall by name style and corruption ({split}, pooled, Wilson 95%)\n")
        out.append("| Stratum | Found recall |")
        out.append("| --- | --- |")
        for s, v in e4["by_style"].items():
            out.append(f"| style {s} | {_rate(v['found_recall'])} |")
        for s, v in e4["by_tag"].items():
            out.append(f"| corruption {s} | {_rate(v['found_recall'])} |")
    e5 = _load(f"E5_{split}")
    if e5:
        out.append(f"\n### E5 placeholder share ({split})\n")
        out.append("| Share | System | LINK precision | LINK F1 | False merges per 10k |")
        out.append("| --- | --- | --- | --- | --- |")
        for share, sys_ in e5["levels"].items():
            for k, v in sys_.items():
                out.append(f"| {share} | {SYSTEM_LABELS.get(k, k)} | {_ci(v['link_precision'], 4)} | "
                           f"{_ci(v['link_f1'], 4)} | {_ci(v['false_merges_per_10k'], 1)} |")  # fmt: skip
    e6 = _load(f"E6_{split}")
    if e6:
        out.append(f"\n### E6 hard negatives ({split}, pooled pairs, Wilson 95%)\n")
        out.append("| Category | System | LINK rate | REVIEW rate |")
        out.append("| --- | --- | --- | --- |")
        for cat, per in e6["categories"].items():
            for k, v in per.items():
                out.append(f"| {cat} | {SYSTEM_LABELS.get(k, k)} | {_rate(v['link_rate'])} | {_rate(v['review_rate'])} |")
    e7 = _load(f"E7_{split}")
    if e7:
        out.append(f"\n### E7 equity ({split}, product, pooled true pairs, Wilson 95%)\n")
        out.append("| Stratum | Found recall | LINK recall |")
        out.append("| --- | --- | --- |")
        for o, v in e7["by_origin"].items():
            out.append(f"| origin {o} | {_rate(v['found_recall'])} | {_rate(v['link_recall'])} |")
        for s, v in e7["by_script_pair"].items():
            out.append(f"| scripts {s} | {_rate(v['found_recall'])} | {_rate(v['link_recall'])} |")
        out.append(f"\nFalse merges by origin of the pair: {e7['false_merges_by_origin']} "
                   f"(total {e7['totals']['false_merges_b5']}).")  # fmt: skip
    e8 = _load(f"E8_{split}")
    if e8:
        out.append(f"\n### E8 independence: G1 against G2 ({split})\n")
        out.append("| System | Found recall G1 | Found recall G2 | Drop | LINK F1 G1 | LINK F1 G2 | False merges per 10k G1 | G2 |")
        out.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
        for k, v in e8["systems"].items():
            out.append(f"| {SYSTEM_LABELS.get(k, k)} | {v['G1']['found_recall']:.4f} | {v['G2']['found_recall']:.4f} | "
                       f"{v['drop_found_recall']:.4f} | {v['G1']['link_f1']:.4f} | {v['G2']['link_f1']:.4f} | "
                       f"{v['G1']['false_merges_per_10k']:.1f} | {v['G2']['false_merges_per_10k']:.1f} |")  # fmt: skip
        out.append(f"\nCalibration error: G1 {e8['ece']['G1']}, G2 {e8['ece']['G2']}.")
    e9 = _load(f"E9_{split}")
    if e9 and e9["default"]:
        out.append(f"\n### E9 review economics ({split}; {e9['units']})\n")
        out.append(f"Costs: {e9['costs']}; simulated reviewer: {e9['reviewer']}.\n")
        out.append("| Quantity | Value |")
        out.append("| --- | --- |")
        for k, v in e9["default"].items():
            out.append(f"| {k.replace('_', ' ')} | {v:.3f} |")
        out.append("\n| Sweep | Value | Reviews per 1k | False merges per 10k | LINK recall | Found recall |")
        out.append("| --- | --- | --- | --- | --- | --- |")
        for key, pts in e9["sweeps"].items():
            for val, m in pts.items():
                out.append(f"| {key} | {val} | {m['review_rate']:.1f} | {m['false_merges_per_10k']:.2f} | "
                           f"{m['link_recall']:.4f} | {m['found_recall']:.4f} |")  # fmt: skip
    h = _load(f"headline_{split}")
    if h:
        out.append(f"\n### Headline run, Tier M ({split}, seeds {h['seeds']['m']})\n")
        out.append(systems_table(h))
    return "\n".join(out)


def sealed_record_block() -> str:
    p = RESULTS / "SEALED_RUN.json"
    if not p.exists():
        return "The sealed run has not happened yet."
    rec = json.loads(p.read_text(encoding="utf-8"))
    return (f"The sealed run happened once, at commit `{rec['commit']}`, started "
            f"{rec['started_at']} and finished {rec['finished_at']} (UTC). Seeds: {rec['seeds']}.")
