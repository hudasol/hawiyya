"""Field comparisons: each record pair gets one discrete level per field.

All functions are pure and symmetric in the order of the two records. A field missing on
either side gives the "missing" level and nothing else: missing data never turns a
disagreement into agreement, and never turns agreement into disagreement.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from rapidfuzz.distance import DamerauLevenshtein, JaroWinkler, Levenshtein

from hawiyya.contract.enums import DatePrecision, IdCapture, IdKind
from hawiyya.normalise.dates import digit_differences, transposed, year_off_by_one
from hawiyya.normalise.names import ParsedName
from hawiyya.normalise.record import NRecord, TermFrequencies
from hawiyya.normalise.text import coarse_key, skeleton_word

from .levels import FIELD_INDEX, FIELDS, N_FIELDS, NAME_LEVELS

LARGE_AGE_GAP_YEARS = 12  # ASSUMPTION: a shared identifier across this gap is a substitute


@dataclass(frozen=True)
class Tok:
    """One name token with its keys, precomputed once per record."""

    text: str
    script: str
    skel: str
    coarse: str


def _tok(text: str | None, script: str) -> Tok | None:
    if not text:
        return None
    k = skeleton_word(text)
    return Tok(text, script, k, coarse_key(k))


@dataclass(frozen=True)
class NameFeat:
    given: Tok | None
    family: Tok | None
    father: Tok | None
    parsed: ParsedName


@dataclass(frozen=True)
class RecFeat:
    rec: NRecord
    names: tuple[NameFeat, ...]


def features(r: NRecord) -> RecFeat:
    names = tuple(
        NameFeat(_tok(n.given, n.script), _tok(n.family, n.script), _tok(n.father, n.script), n)
        for n in r.names
    )
    return RecFeat(r, names)


# ----------------------------------------------------------------------------- names

_EXACT, _SKEL, _COARSE, _EDIT1, _INITIAL, _MISSING, _MISMATCH = range(len(NAME_LEVELS))


def token_level(a: Tok | None, b: Tok | None) -> int:
    """Level index for two name tokens (symmetric)."""
    if a is None or b is None:
        return _MISSING
    if a.script == b.script and a.text == b.text:
        return _EXACT
    if a.skel and a.skel == b.skel:
        return _SKEL
    if a.coarse and a.coarse == b.coarse:
        return _COARSE
    if a.script == b.script == "latin":
        if len(a.text) == 1 or len(b.text) == 1:
            short, long_ = (a, b) if len(a.text) <= len(b.text) else (b, a)
            if long_.text.startswith(short.text):
                return _INITIAL
            return _MISMATCH
        if min(len(a.text), len(b.text)) >= 4 and Levenshtein.distance(a.text, b.text) <= 1:
            return _EDIT1
    if min(len(a.skel), len(b.skel)) >= 3 and Levenshtein.distance(a.skel, b.skel) <= 1:
        return _EDIT1
    return _MISMATCH


def _best_pair(fa: NameFeat, fb: NameFeat) -> tuple[int, int, int]:
    straight = (token_level(fa.given, fb.given), token_level(fa.family, fb.family))
    swapped = (token_level(fa.given, fb.family), token_level(fa.family, fb.given))
    g, f = straight
    # A swapped order is used only when both swapped tokens agree and straight does not. The
    # pair is sorted so the result does not depend on which record comes first.
    if sum(swapped) < sum(straight) and max(swapped) <= _EDIT1:
        g, f = min(swapped), max(swapped)
    return g, f, token_level(fa.father, fb.father)


def name_levels(a: RecFeat, b: RecFeat) -> tuple[int, int, int]:
    """Best (given, family, father) levels over the name renderings both records hold."""
    if not a.names or not b.names:
        return _MISSING, _MISSING, _MISSING
    cands = [_best_pair(fa, fb) for fa in a.names for fb in b.names]
    return min(cands, key=lambda c: (sum(c), c))


def whole_name_level(a: RecFeat, b: RecFeat) -> int:
    sims = [
        JaroWinkler.normalized_similarity(" ".join(fa.parsed.tokens), " ".join(fb.parsed.tokens))
        for fa in a.names
        for fb in b.names
        if fa.parsed.script == fb.parsed.script == "latin"
    ]
    if not sims:
        return 3
    s = max(sims)
    return 0 if s >= 0.95 else 1 if s >= 0.88 else 2


# ----------------------------------------------------------------------------- dob, ids


def dob_level(a: NRecord, b: NRecord) -> int:
    lv = FIELDS[FIELD_INDEX["dob"]].levels
    da, db = a.dob, b.dob
    if da is None or db is None:
        return lv.index("missing")
    if a.dob_placeholder or b.dob_placeholder:
        return lv.index("placeholder")
    if DatePrecision.YEAR in (da.precision, db.precision):
        return lv.index("year_only") if da.year == db.year else lv.index("conflict")
    if da.iso == db.iso:
        return lv.index("exact")
    if transposed(da, db):
        return lv.index("transposed")
    if digit_differences(da, db) == 1:
        return lv.index("digit1")
    if year_off_by_one(da, db):
        return lv.index("year_off")
    return lv.index("conflict")


def _age_gap(a: NRecord, b: NRecord) -> float | None:
    if a.dob is None or b.dob is None:
        return None
    return abs(a.dob.year - b.dob.year) + abs(a.dob.month - b.dob.month) / 12.0


def id_level(a: NRecord, b: NRecord) -> int:
    lv = FIELDS[FIELD_INDEX["identifier"]].levels
    ia, ib = a.ident, b.ident
    if ia.value is None or ib.value is None:
        return lv.index("missing")
    if ia.placeholder or ib.placeholder:
        return lv.index("placeholder")
    substitute = IdKind.MOTHER_EID in (ia.kind, ib.kind)
    if ia.value == ib.value:
        gap = _age_gap(a, b)
        if substitute or (gap is not None and gap >= LARGE_AGE_GAP_YEARS):
            return lv.index("shared_substitute")
        return lv.index("exact")
    kinds = {ia.kind, ib.kind} - {IdKind.MOTHER_EID}
    if substitute or len(kinds) > 1:
        return lv.index("different_kinds")
    if DamerauLevenshtein.distance(ia.value, ib.value) <= 1:
        return lv.index("edit1")
    if ia.capture == IdCapture.READER and ib.capture == IdCapture.READER:
        return lv.index("different_reader")
    return lv.index("different_manual")


def _simple(a: object, b: object) -> int:
    """agree or exact = 0, missing = 1, different = 2."""
    if a is None or b is None:
        return 1
    return 0 if a == b else 2


def compare_pair(a: RecFeat, b: RecFeat) -> np.ndarray:
    """Level index per field (array of length N_FIELDS)."""
    out = np.empty(N_FIELDS, dtype=np.int8)
    g, f, fa = name_levels(a, b)
    out[FIELD_INDEX["given"]] = g
    out[FIELD_INDEX["family"]] = f
    out[FIELD_INDEX["father"]] = fa
    out[FIELD_INDEX["whole_name"]] = whole_name_level(a, b)
    out[FIELD_INDEX["dob"]] = dob_level(a.rec, b.rec)
    ra, rb = a.rec, b.rec
    out[FIELD_INDEX["sex"]] = _simple(ra.sex, rb.sex)
    out[FIELD_INDEX["identifier"]] = id_level(ra, rb)
    out[FIELD_INDEX["phone"]] = _simple(ra.phone, rb.phone)
    out[FIELD_INDEX["nationality"]] = _simple(ra.nationality, rb.nationality)
    out[FIELD_INDEX["area"]] = _simple(ra.area, rb.area)
    return out


def compare_pairs(feats: Sequence[RecFeat], pairs: np.ndarray) -> np.ndarray:
    """Level matrix (n_pairs, N_FIELDS) for an array of index pairs."""
    out = np.empty((len(pairs), N_FIELDS), dtype=np.int8)
    for k, (i, j) in enumerate(pairs):
        out[k] = compare_pair(feats[int(i)], feats[int(j)])
    return out


# ----------------------------------------------------------------------------- frequencies

TF_FIELDS = ("given", "family", "dob", "phone")
_AGREE_NAME = (_EXACT, _SKEL)


def _shared_key(ka: frozenset[str], kb: frozenset[str], tf: TermFrequencies, table: str) -> float:
    shared = sorted(ka & kb)
    if not shared:
        return float("nan")
    # A key may sit in the other table when the order was swapped; use the larger frequency.
    return max(max(tf.get("given", k), tf.get("family", k)) for k in shared)


def tf_values(a: RecFeat, b: RecFeat, lv: np.ndarray, tf: TermFrequencies) -> np.ndarray:
    """Registry frequency of the agreeing value per TF field, or NaN when not applicable.

    For names the most frequent shared skeleton key is used (the conservative choice when a
    record holds several renderings). Symmetric in record order.
    """
    out = np.full(len(TF_FIELDS), np.nan)
    ra, rb = a.rec, b.rec
    if int(lv[FIELD_INDEX["given"]]) in _AGREE_NAME:
        out[0] = _shared_key(ra.given_keys | ra.family_keys, rb.given_keys | rb.family_keys,
                             tf, "given")
    if int(lv[FIELD_INDEX["family"]]) in _AGREE_NAME:
        out[1] = _shared_key(ra.family_keys | ra.given_keys, rb.family_keys | rb.given_keys,
                             tf, "family")
    if int(lv[FIELD_INDEX["dob"]]) == 0 and ra.dob is not None:
        out[2] = tf.get("dob", ra.dob.iso)
    if int(lv[FIELD_INDEX["phone"]]) == 0 and ra.phone is not None:
        out[3] = tf.get("phone", ra.phone)
    return out


def compare_with_tf(feats: Sequence[RecFeat], pairs: np.ndarray,
                    tf: TermFrequencies) -> tuple[np.ndarray, np.ndarray]:
    """Levels and term frequency values for an array of index pairs."""
    levels = np.empty((len(pairs), N_FIELDS), dtype=np.int8)
    tfv = np.empty((len(pairs), len(TF_FIELDS)), dtype=np.float64)
    for k, (i, j) in enumerate(pairs):
        a, b = feats[int(i)], feats[int(j)]
        lv = compare_pair(a, b)
        levels[k] = lv
        tfv[k] = tf_values(a, b, lv, tf)
    return levels, tfv
