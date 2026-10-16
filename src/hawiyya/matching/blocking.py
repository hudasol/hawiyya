"""Multi pass blocking: candidate pairs from several keys, united.

Passes (each record may give several keys per pass):

1. ``family_year``: family name skeleton and birth year.
2. ``given_dob``: given name skeleton and full date of birth.
3. ``id_tail`` and ``id_head``: the last seven and first eleven characters of a usable
   (non placeholder) identifier, so one typo still meets the other half.
4. ``phone``: the full normalised phone number.
5. ``name_pair``: the sorted pair of given and family coarse keys (catches script variants
   and swapped order without a date).
6. ``dob_family``: date of birth and family coarse key (catches a changed given name).

Placeholder identifiers never produce a key. A block larger than the cap is not expanded in
full: its records are sorted by a secondary key and each is paired with its next
``window`` neighbours (sorted neighbourhood fallback).
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field

import numpy as np

from hawiyya.normalise.record import NRecord
from hawiyya.normalise.text import coarse_key

PASSES = ("family_year", "given_dob", "id_tail", "id_head", "phone", "name_pair", "dob_family")
DEFAULT_CAP = 60  # ASSUMPTION: largest block expanded in full
DEFAULT_WINDOW = 12  # ASSUMPTION: neighbours per record in an oversized block


def record_keys(r: NRecord) -> Iterator[tuple[str, str]]:
    """Yield (pass, key) for one record. Never yields a key from a placeholder identifier."""
    year = r.dob.year if r.dob else None
    for fk in sorted(r.family_keys):
        if year is not None and fk:
            yield "family_year", f"{fk}|{year}"
        if r.dob is not None and fk:
            yield "dob_family", f"{r.dob.iso}|{coarse_key(fk)}"
    if r.dob is not None:
        for gk in sorted(r.given_keys):
            if gk:
                yield "given_dob", f"{gk}|{r.dob.iso}"
    uid = r.usable_id
    if uid is not None and len(uid) >= 8:
        yield "id_tail", uid[-7:]
        if len(uid) >= 12:
            yield "id_head", uid[:11]
    if r.phone and len(r.phone) >= 7:
        yield "phone", r.phone
    for n in r.names:
        if n.given_key and n.family_key:
            a, b = sorted((coarse_key(n.given_key), coarse_key(n.family_key)))
            yield "name_pair", f"{a}|{b}"


def _sort_key(r: NRecord) -> str:
    g = sorted(r.given_keys)[0] if r.given_keys else ""
    return f"{g}|{r.dob.iso if r.dob else ''}|{r.record_id}"


@dataclass
class BlockingResult:
    pairs: np.ndarray  # (n, 2) int32, i < j, sorted and unique
    n_records: int
    per_pass: dict[str, int] = field(default_factory=dict)
    capped_blocks: int = 0
    largest_block: int = 0

    @property
    def reduction_ratio(self) -> float:
        total = self.n_records * (self.n_records - 1) / 2
        return 1.0 - len(self.pairs) / total if total else 0.0

    @property
    def pairs_per_record(self) -> float:
        return len(self.pairs) / self.n_records if self.n_records else 0.0


def _encode(i: np.ndarray, j: np.ndarray, n: int) -> np.ndarray:
    lo, hi = np.minimum(i, j), np.maximum(i, j)
    out: np.ndarray = lo.astype(np.int64) * n + hi.astype(np.int64)
    return out


def block(recs: Sequence[NRecord], cap: int = DEFAULT_CAP, window: int = DEFAULT_WINDOW,
          passes: Sequence[str] = PASSES) -> BlockingResult:
    """Candidate pairs for a registry (indices into ``recs``)."""
    n = len(recs)
    blocks: dict[tuple[str, str], list[int]] = defaultdict(list)
    for idx, r in enumerate(recs):
        for p, k in set(record_keys(r)):
            if p in passes:
                blocks[(p, k)].append(idx)
    codes: list[np.ndarray] = []
    per_pass: dict[str, int] = defaultdict(int)
    capped = largest = 0
    for (p, _), members in blocks.items():
        m = len(members)
        if m < 2:
            continue
        largest = max(largest, m)
        arr = np.array(sorted(members), dtype=np.int64)
        if m <= cap:
            ii, jj = np.triu_indices(m, k=1)
            enc = _encode(arr[ii], arr[jj], n)
        else:
            capped += 1
            order = sorted(members, key=lambda x: _sort_key(recs[x]))
            sarr = np.array(order, dtype=np.int64)
            parts = [_encode(sarr[:-w], sarr[w:], n) for w in range(1, min(window, m - 1) + 1)]
            enc = np.concatenate(parts)
        per_pass[p] += len(enc)
        codes.append(enc)
    if codes:
        uniq = np.unique(np.concatenate(codes))
        pairs = np.stack([uniq // n, uniq % n], axis=1).astype(np.int32)
    else:
        pairs = np.empty((0, 2), dtype=np.int32)
    return BlockingResult(pairs, n, dict(per_pass), capped, largest)


def pair_completeness(pairs: np.ndarray, true_pairs: np.ndarray, n: int) -> float:
    """Share of true pairs (index pairs) present among the candidates."""
    if len(true_pairs) == 0:
        return 1.0
    cand = _encode(pairs[:, 0], pairs[:, 1], n)
    tru = _encode(true_pairs[:, 0], true_pairs[:, 1], n)
    return float(np.isin(tru, cand).mean())
