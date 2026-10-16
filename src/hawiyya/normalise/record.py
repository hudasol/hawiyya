"""Record level normalisation, learned placeholders and term frequency tables.

``normalise_registry`` turns registration records into ``NRecord`` objects and builds the
registry context: the data driven (learned) placeholder sets and the term frequency tables.
Everything here is computed from the registration view alone.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field, replace

from hawiyya.contract.enums import DatePrecision, IdKind, Sex
from hawiyya.contract.models import Record
from hawiyya.normalise.dates import Dob, is_pattern_placeholder, parse_dob
from hawiyya.normalise.identifiers import NormId, normalise_identifier
from hawiyya.normalise.names import ParsedName, parse_name
from hawiyya.normalise.text import coarse_key, skeleton_word


@dataclass(frozen=True)
class NRecord:
    record_id: str
    facility_id: str
    names: tuple[ParsedName, ...]
    sex: Sex | None
    dob: Dob | None
    dob_placeholder: bool
    ident: NormId
    phone: str | None
    nationality: str | None
    area: str | None

    @property
    def given_keys(self) -> frozenset[str]:
        return frozenset(n.given_key for n in self.names if n.given_key)

    @property
    def family_keys(self) -> frozenset[str]:
        return frozenset(n.family_key for n in self.names if n.family_key)

    @property
    def father_keys(self) -> frozenset[str]:
        return frozenset(skeleton_word(n.father) for n in self.names if n.father)

    @property
    def usable_id(self) -> str | None:
        """Identifier value that may carry evidence (never a placeholder)."""
        if self.ident.value is None or self.ident.placeholder:
            return None
        return self.ident.value


def normalise_phone(p: str | None) -> str | None:
    if not p:
        return None
    digits = "".join(ch for ch in p if ch.isdigit())
    if digits.startswith("971"):
        digits = "0" + digits[3:]
    if digits.startswith("00971"):
        digits = "0" + digits[5:]
    return digits or None


def normalise_record(r: Record) -> NRecord:
    names = tuple(n for n in (parse_name(r.name_ar), parse_name(r.name_latin)) if n is not None)
    dob = parse_dob(r.dob, r.dob_precision)
    return NRecord(
        record_id=r.record_id,
        facility_id=r.facility_id,
        names=names,
        sex=r.sex if r.sex != Sex.UNKNOWN else None,
        dob=dob,
        dob_placeholder=bool(dob and is_pattern_placeholder(dob)),
        ident=normalise_identifier(r.id_value, r.id_kind, r.id_capture),
        phone=normalise_phone(r.phone),
        nationality=r.nationality,
        area=r.area,
    )


# ----------------------------------------------------------------------------- learned


@dataclass(frozen=True)
class LearnedPlaceholders:
    """Values that the data suggest are placeholders.

    Identifier rule: a value shared by at least ``min_records`` records whose given name
    coarse keys and birth years both take at least ``min_distinct`` distinct values.
    Date rule: a month and day (for example 01-01) whose share of records is at least
    ``dob_ratio`` times the uniform expectation is flagged as a suspected default.
    """

    identifiers: frozenset[str]
    month_days: frozenset[str]
    evidence: dict[str, dict[str, int]] = field(default_factory=dict)


def learn_placeholders(recs: Sequence[NRecord], min_records: int = 3, min_distinct: int = 3,
                       dob_ratio: float = 3.0) -> LearnedPlaceholders:
    groups: dict[str, list[NRecord]] = defaultdict(list)
    for r in recs:
        # A declared newborn substitute legitimately shares the mother's identifier, so it is
        # not counted (several newborns of one mother would otherwise look like a placeholder).
        if r.ident.value and not r.ident.placeholder and r.ident.kind != IdKind.MOTHER_EID:
            groups[r.ident.value].append(r)
    flagged: set[str] = set()
    evidence: dict[str, dict[str, int]] = {}
    for v, rs in groups.items():
        if len(rs) < min_records:
            continue
        years = {r.dob.year for r in rs if r.dob}
        givens = {coarse_key(k) for r in rs for k in sorted(r.given_keys)[:1]}
        if len(years) >= min_distinct and len(givens) >= min_distinct:
            flagged.add(v)
            evidence[v] = {"records": len(rs), "birth_years": len(years), "given_keys": len(givens)}
    md = Counter(f"{r.dob.month:02d}-{r.dob.day:02d}" for r in recs
                 if r.dob and r.dob.precision == DatePrecision.DAY)  # fmt: skip
    total = sum(md.values())
    expected = total / 365.25 if total else 0.0
    month_days = frozenset(k for k, c in md.items() if expected and c >= dob_ratio * expected
                           and c >= 10)  # fmt: skip
    return LearnedPlaceholders(frozenset(flagged), month_days, evidence)


def apply_learned(r: NRecord, learned: LearnedPlaceholders) -> NRecord:
    ident = r.ident
    if ident.value and ident.value in learned.identifiers and not ident.placeholder:
        ident = replace(ident, placeholder=True, kind=IdKind.PLACEHOLDER)
    dob_ph = r.dob_placeholder
    if r.dob and f"{r.dob.month:02d}-{r.dob.day:02d}" in learned.month_days:
        dob_ph = True
    if ident is r.ident and dob_ph == r.dob_placeholder:
        return r
    return replace(r, ident=ident, dob_placeholder=dob_ph)


# ----------------------------------------------------------------------------- frequencies


@dataclass(frozen=True)
class TermFrequencies:
    """Relative frequencies of name keys, dates of birth and phone suffixes in the registry."""

    given: dict[str, float]
    family: dict[str, float]
    dob: dict[str, float]
    phone: dict[str, float]
    n_records: int

    def get(self, table: str, key: str, floor: float = 1e-5) -> float:
        tab: dict[str, float] = getattr(self, table)
        return max(tab.get(key, 0.0), floor)


def _rel(c: Counter[str]) -> dict[str, float]:
    total = sum(c.values())
    return {k: v / total for k, v in c.items()} if total else {}


def build_tf(recs: Iterable[NRecord]) -> TermFrequencies:
    given: Counter[str] = Counter()
    family: Counter[str] = Counter()
    dob: Counter[str] = Counter()
    phone: Counter[str] = Counter()
    n = 0
    for r in recs:
        n += 1
        for k in r.given_keys:
            given[k] += 1
        for k in r.family_keys:
            family[k] += 1
        if r.dob and r.dob.precision == DatePrecision.DAY:
            dob[r.dob.iso] += 1
        if r.phone:
            phone[r.phone] += 1
    return TermFrequencies(_rel(given), _rel(family), _rel(dob), _rel(phone), n)


@dataclass(frozen=True)
class RegistryContext:
    records: tuple[NRecord, ...]
    learned: LearnedPlaceholders
    tf: TermFrequencies

    def by_id(self) -> dict[str, NRecord]:
        return {r.record_id: r for r in self.records}


def normalise_registry(records: Iterable[Record]) -> RegistryContext:
    base = [normalise_record(r) for r in records]
    learned = learn_placeholders(base)
    recs = tuple(apply_learned(r, learned) for r in base)
    return RegistryContext(recs, learned, build_tf(recs))
