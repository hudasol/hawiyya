"""Baseline policies and the shared pair universe.

Every policy is a pure function: registry data in, a decision code per pair of the universe
out (0 keep apart, 1 review, 2 link). Codes and the universe are numpy arrays; nothing is
mutated.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from rapidfuzz.fuzz import token_set_ratio
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import HistGradientBoostingClassifier

from hawiyya.contract.models import Costs, Record
from hawiyya.decision.batch import decide_batch
from hawiyya.decision.cluster import CONTRADICTION_LOG_ODDS, cluster
from hawiyya.decision.costs import DEFAULT_COSTS, KEEP, LINK, REVIEW, decide_codes
from hawiyya.matching.compare import compare_with_tf, features
from hawiyya.matching.levels import FIELD_INDEX, FIELDS, spec
from hawiyya.normalise.identifiers import normalise_value
from hawiyya.normalise.names import parse_name
from hawiyya.scoring.pipeline import Prepared, Scored
from hawiyya.scoring.scorer import Model, Scorer, score_arrays

FUZZY_THRESHOLD = 90  # token set similarity for B2 (ASSUMPTION)
FORCED_THRESHOLD = 0.5


def encode(i: np.ndarray, j: np.ndarray, n: int) -> np.ndarray:
    lo, hi = np.minimum(i, j), np.maximum(i, j)
    out: np.ndarray = lo.astype(np.int64) * n + hi.astype(np.int64)
    return out


@dataclass(frozen=True)
class Universe:
    """Union of Hawiyya candidates, equal identifier pairs and equal name and date pairs."""

    pairs: np.ndarray  # (m, 2) int64, i < j
    codes: np.ndarray  # (m,) int64 encoded
    n: int
    cand_index: np.ndarray  # position in prep.pairs for each universe pair, or -1


def _group_pairs(keys: Sequence[str | None], n: int) -> np.ndarray:
    groups: dict[str, list[int]] = defaultdict(list)
    for idx, k in enumerate(keys):
        if k:
            groups[k].append(idx)
    parts = []
    for members in groups.values():
        if len(members) > 1:
            arr = np.array(members, dtype=np.int64)
            ii, jj = np.triu_indices(len(arr), k=1)
            parts.append(encode(arr[ii], arr[jj], n))
    return np.concatenate(parts) if parts else np.empty(0, dtype=np.int64)


def name_strings(r: Record) -> set[str]:
    out = set()
    for raw in (r.name_ar, r.name_latin):
        p = parse_name(raw)
        if p is not None:
            out.add(" ".join(p.tokens))
    return out


def build_universe(prep: Prepared) -> Universe:
    recs = prep.records
    n = len(recs)
    cand = encode(prep.pairs[:, 0], prep.pairs[:, 1], n)
    ids = _group_pairs([normalise_value(r.id_value) for r in recs], n)
    keys: list[str | None] = []
    expanded: list[int] = []
    for idx, r in enumerate(recs):
        for s in sorted(name_strings(r)):
            if r.dob:
                keys.append(f"{s}|{r.dob}")
                expanded.append(idx)
    groups: dict[str, list[int]] = defaultdict(list)
    for k, idx in zip(keys, expanded, strict=True):
        if k:
            groups[k].append(idx)
    parts = [ids, cand]
    for members in groups.values():
        m = sorted(set(members))
        if len(m) > 1:
            arr = np.array(m, dtype=np.int64)
            ii, jj = np.triu_indices(len(arr), k=1)
            parts.append(encode(arr[ii], arr[jj], n))
    codes = np.unique(np.concatenate(parts))
    pairs = np.stack([codes // n, codes % n], axis=1)
    order = np.argsort(cand)
    pos = np.searchsorted(cand[order], codes)
    pos = np.clip(pos, 0, max(len(cand) - 1, 0))
    found = (cand[order][pos] == codes) if len(cand) else np.zeros(len(codes), dtype=bool)
    cand_index = np.where(found, order[pos], -1)
    return Universe(pairs, codes, n, cand_index)


# ----------------------------------------------------------------------------- policies


def b0_eid_exact(u: Universe, recs: Sequence[Record]) -> np.ndarray:
    ids = [normalise_value(r.id_value) for r in recs]
    table: dict[str, int] = {}
    code = np.array([table.setdefault(v, len(table)) if v is not None else -1 for v in ids])
    a, b = code[u.pairs[:, 0]], code[u.pairs[:, 1]]
    out: np.ndarray = np.where((a >= 0) & (a == b), LINK, KEEP).astype(np.int8)
    return out


def b1_name_dob_exact(u: Universe, recs: Sequence[Record]) -> np.ndarray:
    names = [name_strings(r) for r in recs]
    out = np.zeros(len(u.pairs), dtype=np.int8)
    for k, (i, j) in enumerate(u.pairs):
        ri, rj = recs[int(i)], recs[int(j)]
        if ri.dob and ri.dob == rj.dob and names[int(i)] & names[int(j)]:
            out[k] = LINK
    return out


def b2_fuzzy_raw(u: Universe, recs: Sequence[Record]) -> np.ndarray:
    out = np.zeros(len(u.pairs), dtype=np.int8)
    for k, (i, j) in enumerate(u.pairs):
        ri, rj = recs[int(i)], recs[int(j)]
        if not ri.dob or ri.dob != rj.dob:
            continue
        best = max((token_set_ratio(x, y) for x in (ri.name_ar, ri.name_latin) if x
                    for y in (rj.name_ar, rj.name_latin) if y), default=0.0)  # fmt: skip
        if best >= FUZZY_THRESHOLD:
            out[k] = LINK
    return out


def _on_candidates(u: Universe, cand_codes: np.ndarray) -> np.ndarray:
    out = np.zeros(len(u.pairs), dtype=np.int8)
    mask = u.cand_index >= 0
    out[mask] = cand_codes[u.cand_index[mask]]
    return out


def b4_forced(u: Universe, sc: Scored) -> np.ndarray:
    codes = np.where(sc.prob >= FORCED_THRESHOLD, LINK, KEEP).astype(np.int8)
    return _on_candidates(u, codes)


def product_candidate_codes(prep: Prepared, sc: Scored, costs: Costs = DEFAULT_COSTS) -> np.ndarray:
    """Hawiyya's final codes on candidate pairs: costs, guards, then conflict aware clusters."""
    bd = decide_batch(prep.pairs, prep.levels, sc.contrib, sc.prob, prep.records, costs)
    ids = prep.record_ids()
    links = [(ids[int(i)], ids[int(j)], float(sc.prob[k]))
             for k, (i, j) in enumerate(prep.pairs) if bd.codes[k] == LINK]  # fmt: skip
    contra = [(ids[int(i)], ids[int(j)]) for k, (i, j) in enumerate(prep.pairs)
              if sc.log_odds[k] < CONTRADICTION_LOG_ODDS or int(bd.guard_bits[k]) != 0]  # fmt: skip
    refused = {(a, b) for a, b, _ in cluster(links, contra).conflict_edges}
    codes = bd.codes.copy()
    for k in np.flatnonzero(codes == LINK):
        i, j = map(int, prep.pairs[k])
        if tuple(sorted((ids[i], ids[j]))) in refused:
            codes[k] = REVIEW
    return codes


def b5_hawiyya(u: Universe, prep: Prepared, sc: Scored, costs: Costs = DEFAULT_COSTS) -> np.ndarray:
    return _on_candidates(u, product_candidate_codes(prep, sc, costs))


# ----------------------------------------------------------------------------- B3


NAME_FIELDS = ("given", "family", "father")
WEAK_NAME_LEVELS = ("skeleton", "coarse", "edit1")


def latin_only_levels(prep: Prepared) -> tuple[np.ndarray, np.ndarray]:
    """Levels and frequencies without Arabic names and without skeleton style matching."""
    stripped = [r.model_copy(update={"name_ar": None}) for r in prep.records]
    from hawiyya.normalise.record import apply_learned, normalise_record

    feats = [features(apply_learned(normalise_record(r), prep.ctx.learned)) for r in stripped]
    levels, tfv = compare_with_tf(feats, prep.pairs, prep.ctx.tf)
    for f in NAME_FIELDS:
        fi = FIELD_INDEX[f]
        weak = [spec(f).index(lv) for lv in WEAK_NAME_LEVELS]
        mask = np.isin(levels[:, fi], weak)
        levels[mask, fi] = spec(f).index("mismatch")
    for col, f in enumerate(("given", "family")):
        mask = levels[:, FIELD_INDEX[f]] != spec(f).index("exact")
        tfv[mask, col] = np.nan
    return levels, tfv


def b3_latin_only(u: Universe, prep: Prepared, model: Model,
                  costs: Costs = DEFAULT_COSTS) -> np.ndarray:
    levels, tfv = latin_only_levels(prep)
    scorer = Scorer(model, prep.ctx.tf)
    lo, contrib = score_arrays(levels, tfv, model.params, scorer.ref)
    prob = model.calibrator.predict(lo)
    bd = decide_batch(prep.pairs, levels, contrib, prob, prep.records, costs)
    return _on_candidates(u, bd.codes)


# ----------------------------------------------------------------------------- B6


def gbm_features(levels: np.ndarray, tfv: np.ndarray) -> np.ndarray:
    blocks = []
    for fi, f in enumerate(FIELDS):
        onehot = np.zeros((len(levels), len(f.levels)))
        onehot[np.arange(len(levels)), levels[:, fi].astype(int)] = 1.0
        blocks.append(onehot)
    blocks.append(np.nan_to_num(-np.log(np.where(np.isnan(tfv), 1.0, tfv)), nan=0.0))
    return np.hstack(blocks)


def fit_gbm(levels: np.ndarray, tfv: np.ndarray, labels: np.ndarray) -> CalibratedClassifierCV:
    base = HistGradientBoostingClassifier(max_iter=150, learning_rate=0.1, random_state=0)
    clf = CalibratedClassifierCV(base, method="isotonic", cv=3)
    clf.fit(gbm_features(levels, tfv), labels.astype(int))
    return clf


def b6_gbm(u: Universe, prep: Prepared, clf: CalibratedClassifierCV,
           costs: Costs = DEFAULT_COSTS) -> np.ndarray:
    prob = clf.predict_proba(gbm_features(prep.levels, prep.tfv))[:, 1]
    return _on_candidates(u, decide_codes(prob, costs))
