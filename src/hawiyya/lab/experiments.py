"""Experiment harness for E1 to E9 and the headline run (see docs/PREREGISTRATION.md).

``run_suite("dev")`` evaluates development seeds; ``run_suite("sealed")`` evaluates the
sealed seeds and may only be called by ``hawiyya eval --sealed``. Seeds run in worker
processes; results are written to ``results/experiments/<E>_<split>.json``.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from collections import Counter, defaultdict
from collections.abc import Iterable
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from hawiyya.contract.models import Costs
from hawiyya.core.paths import RESULTS, ROOT, VAR
from hawiyya.core.sealed import DEV_SEEDS, SEALED_SEEDS, sealed_access
from hawiyya.decision.costs import DEFAULT_COSTS, LINK, REVIEW
from hawiyya.lab import baselines as B
from hawiyya.lab.metrics import bcubed, ece, mean_ci, pair_counts, wilson
from hawiyya.lab.train import FIT_SEEDS, load_model, load_seed
from hawiyya.matching.blocking import block, pair_completeness
from hawiyya.registry.build import build_registry
from hawiyya.registry.truth import HARD_NEGATIVES
from hawiyya.scoring.calibration import fit_isotonic
from hawiyya.scoring.em import fit_anchored
from hawiyya.scoring.pipeline import prepare, score_prepared
from hawiyya.scoring.scorer import Model, Scorer, score_arrays
from hawiyya.workflow.reviewer import ReviewerModel, simulate

SYSTEMS = ("B0_eid_exact", "B1_name_dob_exact", "B2_fuzzy_raw", "B3_latin_only", "B4_forced",
           "B5_hawiyya", "B6_gbm")  # fmt: skip
CORE = ("B0_eid_exact", "B4_forced", "B5_hawiyya")
SHARES = (0.0, 0.1, 0.2, 0.3, 0.4)
COVERAGES = (0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.5, 0.75, 1.0)
SWEEPS: dict[str, tuple[float, ...]] = {
    "c_fm": (50, 100, 250, 500, 1000, 2000, 5000),
    "c_md": (5, 10, 20, 50, 100),
    "c_r": (0.5, 1, 2, 5, 10),
}
REVIEWER = ReviewerModel(accuracy=0.97, minutes_per_case=4.0)
OUT = RESULTS / "experiments"

PLAN: dict[str, dict[str, Any]] = {
    "dev": {
        "g1": DEV_SEEDS[5:25], "g2": DEV_SEEDS[5:15], "e5": DEV_SEEDS[5:10],
        "sweep": DEV_SEEDS[5:10], "headline": DEV_SEEDS[25:30],
    },
    "sealed": {
        "g1": SEALED_SEEDS[0:20], "g2": SEALED_SEEDS[20:30], "e5": SEALED_SEEDS[0:5],
        "sweep": SEALED_SEEDS[0:5], "headline": (),
    },
}  # fmt: skip


@dataclass
class Fitted:
    model: Model
    b3: Model
    gbm: Any


def fit_all() -> Fitted:
    """Frozen product model plus the B3 refit and the B6 reference, all on fit seeds."""
    model = load_model()
    fit = [load_seed(s) for s in FIT_SEEDS]
    lt = [B.latin_only_levels(d.prep) for d in fit]
    levels = np.concatenate([x[0] for x in lt])
    labels = np.concatenate([d.labels for d in fit])
    params = fit_anchored(levels).params
    los = []
    for d, (lv, tfv) in zip(fit, lt, strict=True):
        ref = Scorer(Model(params, model.calibrator), d.prep.ctx.tf).ref
        los.append(score_arrays(lv, tfv, params, ref)[0])
    b3 = Model(params, fit_isotonic(np.concatenate(los), labels.astype(float)))
    gbm = B.fit_gbm(np.concatenate([d.prep.levels for d in fit]),
                    np.concatenate([d.prep.tfv for d in fit]), labels)  # fmt: skip
    return Fitted(model, b3, gbm)


# ----------------------------------------------------------------------------- per seed


def _script(r: Any) -> str:
    if r.name_ar and r.name_latin:
        return "both"
    return "ar" if r.name_ar else "latin" if r.name_latin else "none"


def evaluate_seed(job: dict[str, Any]) -> dict[str, Any]:
    if job.get("sealed"):
        with sealed_access():
            return _evaluate(job)
    return _evaluate(job)


def _evaluate(job: dict[str, Any]) -> dict[str, Any]:
    t0 = time.perf_counter()
    fitted: Fitted = job["fitted"]
    reg = build_registry(job["seed"], job["tier"], generator=job["generator"],
                         placeholder_share=job.get("share"))  # fmt: skip
    prep = prepare(reg.records)
    sc = score_prepared(prep, fitted.model)
    recs = prep.records
    ids = prep.record_ids()
    pid_map: dict[str, int] = {}
    person = np.array([pid_map.setdefault(reg.truth.person_of(r), len(pid_map)) for r in ids])
    n = len(recs)
    true_pairs = reg.truth.true_pairs()
    n_true = len(true_pairs)
    u = B.build_universe(prep)
    y_u = person[u.pairs[:, 0]] == person[u.pairs[:, 1]]
    y_c = person[prep.pairs[:, 0]] == person[prep.pairs[:, 1]]
    codes: dict[str, np.ndarray] = {}
    systems = job["systems"]
    if "B0_eid_exact" in systems:
        codes["B0_eid_exact"] = B.b0_eid_exact(u, recs)
    if "B1_name_dob_exact" in systems:
        codes["B1_name_dob_exact"] = B.b1_name_dob_exact(u, recs)
    if "B2_fuzzy_raw" in systems:
        codes["B2_fuzzy_raw"] = B.b2_fuzzy_raw(u, recs)
    if "B3_latin_only" in systems:
        codes["B3_latin_only"] = B.b3_latin_only(u, prep, fitted.b3)
    if "B4_forced" in systems:
        codes["B4_forced"] = B.b4_forced(u, sc)
    cand_b5 = B.product_candidate_codes(prep, sc)
    codes["B5_hawiyya"] = B._on_candidates(u, cand_b5)
    if "B6_gbm" in systems:
        codes["B6_gbm"] = B.b6_gbm(u, prep, fitted.gbm)
    out: dict[str, Any] = {"seed": job["seed"], "generator": job["generator"],
                           "tier": job["tier"], "share": job.get("share"),
                           "n_records": n, "n_true": n_true, "systems": {}}  # fmt: skip
    for name, c in codes.items():
        m = pair_counts(c, y_u, n_true, n)
        link_pairs = u.pairs[c == LINK]
        m["bcubed_precision"], m["bcubed_recall"] = bcubed(link_pairs, person)
        out["systems"][name] = m
    # E1 blocking
    idx = {rid: i for i, rid in enumerate(ids)}
    tp_arr = np.array(sorted((min(idx[a], idx[b]), max(idx[a], idx[b])) for a, b in true_pairs))
    out["blocking"] = {
        "pair_completeness": pair_completeness(prep.pairs, tp_arr, n),
        "reduction_ratio": prep.blocking.reduction_ratio,
        "pairs_per_record": prep.blocking.pairs_per_record,
    }
    if job.get("cap_cost"):
        full = block(prep.ctx.records, cap=10**9)
        out["blocking"]["pc_lost_to_cap"] = (pair_completeness(full.pairs, tp_arr, n)
                                             - out["blocking"]["pair_completeness"])  # fmt: skip
    # E3 calibration and abstention
    p = sc.prob
    out["calibration"] = {
        "ece": ece(p, y_c.astype(float)),
        "review_share": float((cand_b5 == REVIEW).mean()) if len(cand_b5) else 0.0,
        "bins": [[float(p[(np.clip((p * 10).astype(int), 0, 9) == b)].sum()),
                  float(y_c[(np.clip((p * 10).astype(int), 0, 9) == b)].sum()),
                  int((np.clip((p * 10).astype(int), 0, 9) == b).sum())] for b in range(10)],
        "risk_coverage": _risk_coverage(p, y_c),
    }  # fmt: skip
    if job.get("strata"):
        out["strata"] = _strata(reg, prep, u, codes, y_u, true_pairs, idx)
    if job.get("sweep"):
        out["sweep"] = _sweeps(prep, sc, u, y_u, n_true, n)
        out["review_sim"] = _review_sim(reg, u, codes["B5_hawiyya"], y_u, job["seed"], ids)
    out["seconds"] = round(time.perf_counter() - t0, 1)
    return out


def _risk_coverage(p: np.ndarray, y: np.ndarray) -> list[list[float]]:
    order = np.argsort(-p, kind="mergesort")
    ys = y[order]
    pts = []
    for c in COVERAGES:
        k = max(1, round(c * len(ys)))
        pts.append([c, float(ys[:k].mean())])
    return pts


def _strata(reg: Any, prep: Any, u: B.Universe, codes: dict[str, np.ndarray], y_u: np.ndarray,
            true_pairs: set[tuple[str, str]], idx: dict[str, int]) -> dict[str, Any]:
    recs = prep.records
    labels = reg.truth.labels
    people = reg.truth.people
    n = len(recs)
    b5 = codes["B5_hawiyya"]
    pos = {int(c): k for k, c in enumerate(u.codes)}
    style: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    tag: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    origin: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0])
    script: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0])
    for a, b in sorted(true_pairs):
        i, j = idx[a], idx[b]
        k = pos.get(min(i, j) * n + max(i, j))
        code = int(b5[k]) if k is not None else 0
        found, linked = int(code >= REVIEW), int(code == LINK)
        la, lb = labels[a], labels[b]
        for s in {la.name_style, lb.name_style}:
            style[s][0] += found
            style[s][1] += 1
        tags = {t for t in (*la.corruption_log, *lb.corruption_log) if t.startswith("name:")}
        for t in tags:
            tag[t][0] += found
            tag[t][1] += 1
        o = people.get(la.person_id).origin.value
        origin[o][0] += found
        origin[o][1] += linked
        origin[o][2] += 1
        sp = "+".join(sorted((_script(recs[i]), _script(recs[j]))))
        script[sp][0] += found
        script[sp][1] += linked
        script[sp][2] += 1
    cats: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(lambda: [0, 0, 0]))
    fm_origin: Counter[str] = Counter()
    neg = np.flatnonzero(~y_u)
    for kk in neg:
        i, j = map(int, u.pairs[kk])
        cat = reg.truth.category(recs[i], recs[j])
        for name, c in codes.items():
            if name not in CORE:
                continue
            cell = cats[cat][name]
            cell[0] += int(c[kk] == LINK)
            cell[1] += int(c[kk] == REVIEW)
            cell[2] += 1
        if b5[kk] == LINK:
            oa = people.get(labels[recs[i].record_id].person_id).origin.value
            ob = people.get(labels[recs[j].record_id].person_id).origin.value
            fm_origin[oa if oa == ob else "mixed"] += 1
    return {
        "style": dict(style), "tag": dict(tag), "origin": dict(origin), "script": dict(script),
        "categories": {c: dict(v) for c, v in cats.items()}, "fm_origin": dict(fm_origin),
    }  # fmt: skip


def _sweeps(prep: Any, sc: Any, u: B.Universe, y_u: np.ndarray, n_true: int,
            n: int) -> dict[str, dict[str, dict[str, float]]]:
    out: dict[str, dict[str, dict[str, float]]] = {}
    for key, values in SWEEPS.items():
        out[key] = {}
        for v in values:
            c = DEFAULT_COSTS.model_copy(update={key: float(v)})
            codes = B._on_candidates(u, B.product_candidate_codes(prep, sc, Costs(**c.model_dump())))
            m = pair_counts(codes, y_u, n_true, n)
            out[key][str(v)] = {k: m[k] for k in ("review_rate", "false_merges_per_10k",
                                                  "link_recall", "found_recall")}  # fmt: skip
    return out


def _review_sim(reg: Any, u: B.Universe, b5: np.ndarray, y_u: np.ndarray, seed: int,
                ids: list[str]) -> dict[str, float]:
    review = u.pairs[b5 == REVIEW]
    pairs = [(ids[int(i)], ids[int(j)]) for i, j in review]
    res = simulate(pairs, reg.truth.is_match, REVIEWER, seed)
    return {"cases": res.cases, "minutes": res.minutes, "reviewer_false_merges": res.false_merges,
            "reviewer_missed": res.missed_duplicates}  # fmt: skip


# ----------------------------------------------------------------------------- aggregation


def _systems_summary(rows: list[dict[str, Any]], systems: Iterable[str]) -> dict[str, Any]:
    keys = ("link_precision", "link_recall", "link_f1", "false_merges_per_10k", "found_recall",
            "review_rate", "bcubed_precision", "bcubed_recall")  # fmt: skip
    out = {}
    for s in systems:
        vals = [r["systems"][s] for r in rows if s in r["systems"]]
        if vals:
            out[s] = {k: mean_ci([v[k] for v in vals]) for k in keys}
    return out


def _pool(rows: list[dict[str, Any]], key: str) -> dict[str, list[int]]:
    pooled: dict[str, list[int]] = {}
    for r in rows:
        for k, v in r["strata"][key].items():
            cur = pooled.setdefault(k, [0] * len(v))
            for i, x in enumerate(v):
                cur[i] += x
    return pooled


def _envelope(exp: str, split: str, seeds: dict[str, list[int]], body: dict[str, Any]) -> dict[str, Any]:
    return {"experiment": exp, "split": split, "seeds": seeds,
            "note": "Synthetic data; generator and method share an author.", **body}  # fmt: skip


def aggregate(split: str, g1: list[dict[str, Any]], g2: list[dict[str, Any]],
              e5: list[dict[str, Any]], headline: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    seeds = {"g1": [r["seed"] for r in g1], "g2": [r["seed"] for r in g2]}
    docs: dict[str, dict[str, Any]] = {}
    gens = {}
    for gname, rows in (("G1", g1), ("G2", g2)):
        if rows:
            bl = [r["blocking"] for r in rows]
            gens[gname] = {k: mean_ci([b[k] for b in bl if k in b])
                           for k in ("pair_completeness", "reduction_ratio", "pairs_per_record",
                                     "pc_lost_to_cap") if any(k in b for b in bl)}  # fmt: skip
    docs["E1"] = _envelope("E1", split, seeds, {"generators": gens})
    docs["E2"] = _envelope("E2", split, {"g1": seeds["g1"]},
                           {"systems": _systems_summary(g1, SYSTEMS)})
    bins = np.zeros((10, 3))
    for r in g1:
        bins += np.array(r["calibration"]["bins"])
    reliability = [{"bin": b / 10, "n": int(bins[b, 2]),
                    "mean_predicted": round(bins[b, 0] / bins[b, 2], 6) if bins[b, 2] else None,
                    "observed": round(bins[b, 1] / bins[b, 2], 6) if bins[b, 2] else None}
                   for b in range(10)]  # fmt: skip
    rc = np.mean([[pt[1] for pt in r["calibration"]["risk_coverage"]] for r in g1], axis=0)
    fit_report = json.loads((RESULTS / "model" / "fit_report.json").read_text(encoding="utf-8"))
    docs["E3"] = _envelope("E3", split, {"g1": seeds["g1"]}, {
        "ece": mean_ci([r["calibration"]["ece"] for r in g1]),
        "auto_link_precision": mean_ci([r["systems"]["B5_hawiyya"]["link_precision"] for r in g1]),
        "review_share": mean_ci([r["calibration"]["review_share"] for r in g1]),
        "reliability": reliability,
        "risk_coverage": [{"coverage": c, "precision": round(float(v), 6)}
                          for c, v in zip(COVERAGES, rc, strict=True)],
        "estimation": {
            "plain_em_lambda": fit_report["plain_em"]["lambda"],
            "anchored_lambda": fit_report["em_anchored"]["lambda"],
            "label_lambda": fit_report["labels"]["lambda"],
            "plain_em_average_precision": fit_report["plain_em"]["average_precision"],
            "anchored_average_precision": fit_report["em_anchored"]["average_precision"],
            "label_average_precision": fit_report["labels"]["average_precision"],
            "plain_em_mean_absolute_weight_gap": fit_report["plain_em"]["mean_absolute_weight_gap"],
            "anchored_mean_absolute_weight_gap": fit_report["em_anchored"]["mean_absolute_weight_gap"],
            "source": "results/model/fit_report.json (fitting seeds 1 to 3, checked on 4 and 5)",
        },
    })  # fmt: skip
    style = _pool(g1, "style")
    tag = _pool(g1, "tag")
    docs["E4"] = _envelope("E4", split, {"g1": seeds["g1"]}, {
        "by_style": {s: {"found_recall": wilson(v[0], v[1])} for s, v in sorted(style.items())},
        "by_tag": {s: {"found_recall": wilson(v[0], v[1])} for s, v in sorted(tag.items())},
        "overall_found_recall": mean_ci([r["systems"]["B5_hawiyya"]["found_recall"] for r in g1]),
    })  # fmt: skip
    levels: dict[str, Any] = {}
    for share in SHARES:
        rows = [r for r in e5 if r["share"] == share]
        levels[str(share)] = _systems_summary(rows, CORE)
    docs["E5"] = _envelope("E5", split, {"e5": sorted({r["seed"] for r in e5})},
                           {"levels": levels})  # fmt: skip
    cats_pooled: dict[str, dict[str, list[int]]] = {}
    for r in g1:
        for cat, per in r["strata"]["categories"].items():
            for sys_name, v in per.items():
                cur = cats_pooled.setdefault(cat, {}).setdefault(sys_name, [0, 0, 0])
                for i, x in enumerate(v):
                    cur[i] += x
    docs["E6"] = _envelope("E6", split, {"g1": seeds["g1"]}, {
        "categories": {c: {s: {"link_rate": wilson(v[0], v[2]), "review_rate": wilson(v[1], v[2])}
                           for s, v in per.items()} for c, per in sorted(cats_pooled.items())},
        "hard_negative_categories": list(HARD_NEGATIVES),
    })  # fmt: skip
    origin = _pool(g1, "origin")
    script = _pool(g1, "script")
    fm: Counter[str] = Counter()
    for r in g1:
        fm.update(r["strata"]["fm_origin"])
    docs["E7"] = _envelope("E7", split, {"g1": seeds["g1"]}, {
        "by_origin": {o: {"found_recall": wilson(v[0], v[2]), "link_recall": wilson(v[1], v[2])}
                      for o, v in sorted(origin.items())},
        "by_script_pair": {s: {"found_recall": wilson(v[0], v[2]), "link_recall": wilson(v[1], v[2])}
                           for s, v in sorted(script.items())},
        "false_merges_by_origin": dict(sorted(fm.items())),
        "totals": {"true_pairs": sum(r["n_true"] for r in g1),
                   "false_merges_b5": sum(r["systems"]["B5_hawiyya"]["fp"] for r in g1)},
    })  # fmt: skip
    if g2:
        s1, s2 = _systems_summary(g1, SYSTEMS), _systems_summary(g2, SYSTEMS)
        systems8 = {}
        for s in SYSTEMS:
            if s in s1 and s in s2:
                systems8[s] = {
                    "G1": {k: s1[s][k]["mean"] for k in ("found_recall", "link_f1", "false_merges_per_10k")},
                    "G2": {k: s2[s][k]["mean"] for k in ("found_recall", "link_f1", "false_merges_per_10k")},
                    "drop_found_recall": round(s1[s]["found_recall"]["mean"] - s2[s]["found_recall"]["mean"], 6),
                    "drop_link_f1": round(s1[s]["link_f1"]["mean"] - s2[s]["link_f1"]["mean"], 6),
                }  # fmt: skip
        docs["E8"] = _envelope("E8", split, seeds, {
            "systems": systems8,
            "ece": {"G1": round(float(np.mean([r["calibration"]["ece"] for r in g1])), 6),
                    "G2": round(float(np.mean([r["calibration"]["ece"] for r in g2])), 6)},
        })  # fmt: skip
    docs["E9"] = _e9(split, g1)
    if headline:
        docs["headline"] = _envelope("headline", split, {"m": [r["seed"] for r in headline]},
                                     {"tier": "M", "systems": _systems_summary(headline, CORE)})
    return docs


def _e9(split: str, g1: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [r for r in g1 if "sweep" in r]
    c = DEFAULT_COSTS
    per = []
    for r in rows:
        m = r["systems"]["B5_hawiyya"]
        n, n_true = r["n_records"], r["n_true"]
        missed = n_true - m["found"]
        sim = r["review_sim"]
        k = 1000 / n
        per.append({
            "reviews_per_1000": m["reviews"] * k,
            "minutes_per_1000": sim["minutes"] * k,
            "residual_false_merges_perfect_per_1000": m["fp"] * k,
            "residual_missed_perfect_per_1000": missed * k,
            "residual_false_merges_reviewer_per_1000": (m["fp"] + sim["reviewer_false_merges"]) * k,
            "residual_missed_reviewer_per_1000": (missed + sim["reviewer_missed"]) * k,
            "cost_hawiyya_perfect_reviewer": (c.c_fm * m["fp"] + c.c_md * missed + c.c_r * m["reviews"]) * k,
            "cost_hawiyya_reviewer": (c.c_fm * (m["fp"] + sim["reviewer_false_merges"])
                                      + c.c_md * (missed + sim["reviewer_missed"])
                                      + c.c_r * m["reviews"]) * k,
            "cost_do_nothing": c.c_md * n_true * k,
        })  # fmt: skip
    default = {key: round(float(np.mean([p[key] for p in per])), 6) for key in per[0]} if per else {}
    sweeps: dict[str, dict[str, dict[str, float]]] = {}
    for key, values in SWEEPS.items():
        sweeps[key] = {}
        for v in values:
            pts = [r["sweep"][key][str(v)] for r in rows]
            sweeps[key][str(v)] = {m: round(float(np.mean([p[m] for p in pts])), 6) for m in pts[0]}
    return _envelope("E9", split, {"sweep": [r["seed"] for r in rows]}, {
        "units": "per 1,000 records; costs in abstract cost units",
        "costs": c.model_dump(), "reviewer": {"accuracy": REVIEWER.accuracy,
                                              "minutes_per_case": REVIEWER.minutes_per_case},
        "default": default, "sweeps": sweeps,
    })  # fmt: skip


# ----------------------------------------------------------------------------- runner


def _jobs(split: str, fitted: Fitted, smoke: bool = False) -> list[dict[str, Any]]:
    plan = PLAN[split]
    sealed = split == "sealed"
    g1 = plan["g1"][:1] if smoke else plan["g1"]
    jobs = []
    for s in g1:
        jobs.append({"kind": "g1", "seed": s, "tier": "S", "generator": "G1", "systems": SYSTEMS,
                     "strata": True, "cap_cost": True, "sweep": s in plan["sweep"],
                     "sealed": sealed, "fitted": fitted})  # fmt: skip
    if smoke:
        return jobs
    for s in plan["g2"]:
        jobs.append({"kind": "g2", "seed": s, "tier": "S", "generator": "G2", "systems": SYSTEMS,
                     "cap_cost": True, "sealed": sealed, "fitted": fitted})  # fmt: skip
    for s in plan["e5"]:
        for share in SHARES:
            jobs.append({"kind": "e5", "seed": s, "tier": "S", "generator": "G1", "share": share,
                         "systems": CORE, "sealed": sealed, "fitted": fitted})  # fmt: skip
    for s in plan["headline"]:
        jobs.append({"kind": "headline", "seed": s, "tier": "M", "generator": "G1",
                     "systems": CORE, "sealed": sealed, "fitted": fitted})  # fmt: skip
    return jobs


def run_suite(split: str, workers: int | None = None, smoke: bool = False,
              out_dir: Path = OUT) -> dict[str, dict[str, Any]]:
    if split == "sealed":
        import inspect

        caller = inspect.stack()[1].function
        if caller != "run_sealed":
            raise PermissionError("the sealed suite runs only through run_sealed")
    fitted = fit_all()
    jobs = _jobs(split, fitted, smoke)
    workers = workers or max(1, min(4, (os.cpu_count() or 2) - 1))
    # Each finished job is cached so an interrupted run resumes; the cache lives in var/
    # (ignored by git) and is keyed by the model version.
    cache = VAR / "eval_cache" / f"{split}_{fitted.model.version}"
    cache.mkdir(parents=True, exist_ok=True)

    def key(job: dict[str, Any]) -> Path:
        return cache / f"{job['kind']}_{job['generator']}_{job['tier']}_{job['seed']}_{job.get('share')}.json"

    results: list[dict[str, Any] | None] = [
        None if smoke or not key(j).exists() else json.loads(key(j).read_text(encoding="utf-8"))
        for j in jobs
    ]
    todo = [i for i, r in enumerate(results) if r is None]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(evaluate_seed, jobs[i]): i for i in todo}
        for fut in as_completed(futures):
            i = futures[fut]
            res = fut.result()
            results[i] = res
            if not smoke:
                key(jobs[i]).write_text(json.dumps(res), encoding="utf-8")
    done = [r for r in results if r is not None]
    by = defaultdict(list)
    for job, res in zip(jobs, done, strict=True):
        by[job["kind"]].append(res)
    for rows in by.values():
        rows.sort(key=lambda r: (r["seed"], r.get("share") or 0.0))
    docs = aggregate(split, by["g1"], by["g2"], by["e5"], by["headline"])
    if not smoke:
        out_dir.mkdir(parents=True, exist_ok=True)
        for name, doc in docs.items():
            (out_dir / f"{name}_{split}.json").write_text(
                json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8",
                newline="\n")
        timing = {"jobs": len(jobs), "seconds_per_job": [r["seconds"] for r in done]}
        (out_dir / f"timing_{split}.json").write_text(json.dumps(timing) + "\n", encoding="utf-8")
    return docs


def _commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                              text=True, check=True).stdout.strip()  # fmt: skip
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def run_sealed(workers: int | None = None) -> dict[str, Any]:
    """The one sealed run. Refuses to run twice."""
    marker = RESULTS / "SEALED_RUN.json"
    if marker.exists():
        raise PermissionError("the sealed run has already happened; see results/SEALED_RUN.json")
    started = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    commit = _commit()
    docs = run_suite("sealed", workers)
    record = {"commit": commit, "started_at": started,
              "finished_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
              "seeds": {k: list(v) for k, v in PLAN["sealed"].items()},
              "files": sorted(f"results/experiments/{k}_sealed.json" for k in docs)}  # fmt: skip
    marker.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")
    return record
