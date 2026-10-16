"""Identity layer: turns a population sample into people with families and identifiers.

This module builds the structure that both generators share: households, clans (cousins),
twins, same name fathers and sons, newborns, origin groups, nationalities, synthetic
identifiers, phones and areas. It does not render names as text: G1 and G2 each render
names with their own rules, so the independence of G2 is not weakened here.

Every rate below is an ASSUMPTION chosen by the author, not a measured value.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date

import numpy as np

from hawiyya.contract.enums import OriginGroup
from hawiyya.core.determinism import rng
from hawiyya.registry.lexicon import TIER_WEIGHT, Lexicon, NameEntry, load_denylist
from hawiyya.registry.source import REFERENCE_DATE, PopulationPerson

ORIGIN_SHARE: dict[OriginGroup, float] = {  # ASSUMPTION
    OriginGroup.GULF_ARAB: 0.30,
    OriginGroup.OTHER_ARAB: 0.20,
    OriginGroup.SOUTH_ASIAN: 0.30,
    OriginGroup.SOUTHEAST_ASIAN: 0.12,
    OriginGroup.WESTERN: 0.08,
}
NATIONALITY: dict[OriginGroup, dict[str, float]] = {  # ASSUMPTION
    OriginGroup.GULF_ARAB: {"ARE": 0.80, "SAU": 0.06, "OMN": 0.07, "BHR": 0.02, "KWT": 0.02, "QAT": 0.03},
    OriginGroup.OTHER_ARAB: {"EGY": 0.30, "JOR": 0.20, "SYR": 0.15, "LBN": 0.10, "SDN": 0.15, "MAR": 0.10},
    OriginGroup.SOUTH_ASIAN: {"IND": 0.55, "PAK": 0.30, "BGD": 0.10, "LKA": 0.05},
    OriginGroup.SOUTHEAST_ASIAN: {"PHL": 0.75, "IDN": 0.20, "MYS": 0.05},
    OriginGroup.WESTERN: {"GBR": 0.40, "USA": 0.20, "FRA": 0.10, "DEU": 0.10, "CAN": 0.10, "AUS": 0.10},
}
GCC_NON_UAE = {"SAU", "OMN", "BHR", "KWT", "QAT"}
ARAB_ORIGINS = {OriginGroup.GULF_ARAB, OriginGroup.OTHER_ARAB}
MEAN_CHILDREN = {OriginGroup.GULF_ARAB: 3.0, OriginGroup.OTHER_ARAB: 2.2}
HOUSEHOLD_FATHER_SHARE = 0.55
MOTHER_SHARE = 0.85
CLAN_SHARE = 0.30
TWIN_SHARE = 0.10
SAME_NAME_SON_SHARE = 0.08
VISITOR_SHARE = 0.12
GCC_WITH_EID_SHARE = 0.5
CHILD_SHARES_PHONE = 0.6
WIFE_TAKES_HUSBAND_NAME = {OriginGroup.SOUTHEAST_ASIAN, OriginGroup.WESTERN}


@dataclass
class Person:
    person_id: str
    sex: str
    birth_date: date
    region: str
    encounters: int
    origin: OriginGroup = OriginGroup.GULF_ARAB
    nationality: str = "ARE"
    given: NameEntry | None = None
    father_given: NameEntry | None = None
    grandfather_given: NameEntry | None = None
    family: NameEntry | None = None
    birth_family: NameEntry | None = None
    family_id: str = ""
    clan_id: str = ""
    role: str = "single"
    father_id: str | None = None
    mother_id: str | None = None
    twin_group: str | None = None
    eid: str | None = None
    passport: str | None = None
    gcc_id: str | None = None
    phone: str | None = None
    area: str = ""
    flags: list[str] = field(default_factory=list)

    def age_on(self, d: date) -> float:
        return (d - self.birth_date).days / 365.25


@dataclass
class People:
    persons: list[Person]
    by_id: dict[str, Person]
    seed: int

    def get(self, pid: str) -> Person:
        return self.by_id[pid]


def _weighted(g: np.random.Generator, entries: list[NameEntry]) -> NameEntry:
    w = np.array([TIER_WEIGHT[e.tier] for e in entries])
    return entries[int(g.choice(len(entries), p=w / w.sum()))]


def _choice(g: np.random.Generator, table: dict[str, float]) -> str:
    keys = list(table)
    p = np.array([table[k] for k in keys])
    return keys[int(g.choice(len(keys), p=p / p.sum()))]


class _Namer:
    def __init__(self, lex: Lexicon, g: np.random.Generator) -> None:
        self.lex, self.g = lex, g
        self.deny = load_denylist()

    def given(self, origin: OriginGroup, sex: str) -> NameEntry:
        pool = self.lex.given_for(origin, sex)
        return _weighted(self.g, pool)

    def family(self, origin: OriginGroup) -> NameEntry:
        return _weighted(self.g, self.lex.family_for(origin))

    def safe_given(self, origin: OriginGroup, sex: str, family: NameEntry) -> NameEntry:
        """Draw a given name, refusing denylisted given and family combinations."""
        for _ in range(50):
            cand = self.given(origin, sex)
            if not self.deny.combination_denied(cand, family):
                return cand
        raise RuntimeError("could not draw an allowed given name")


def _eid(g: np.random.Generator, birth: date, used: set[str]) -> str:
    """Synthetic 15 digit identifier: 784, birth year, 8 random digits. No check digit.

    The values are generated, are not drawn from any registry, and could coincide with a real
    number only by chance. The check digit rule was not taken from any source, so none is
    computed (see the data statement).
    """
    while True:
        v = f"784{birth.year:04d}{int(g.integers(0, 10**8)):08d}"
        if v not in used:
            used.add(v)
            return v


def _passport(g: np.random.Generator, used: set[str]) -> str:
    letters = "ABCDEFGHJKLMNPRSTUVWXYZ"
    while True:
        v = letters[int(g.integers(0, 23))] + letters[int(g.integers(0, 23))]
        v += f"{int(g.integers(0, 10**7)):07d}"
        if v not in used:
            used.add(v)
            return v


def _gcc(g: np.random.Generator, used: set[str]) -> str:
    while True:
        v = f"{int(g.integers(10**9, 10**10))}"
        if v not in used:
            used.add(v)
            return v


def _phone(g: np.random.Generator) -> str:
    return f"05{int(g.choice([0, 2, 4, 5, 6, 8]))}{int(g.integers(0, 10**7)):07d}"


def build_people(pop: list[PopulationPerson], lex: Lexicon, seed: int) -> People:
    """Assign households, clans, twins, names (as lexicon entries) and identifiers."""
    g = rng(seed, "people")
    namer = _Namer(lex, g)
    order = g.permutation(len(pop))
    persons = [
        Person(p.person_id, p.sex, p.birth_date, p.region, p.encounters)
        for p in (pop[int(i)] for i in order)
    ]
    by_id = {p.person_id: p for p in persons}
    free = {p.person_id for p in persons}
    by_year: dict[int, list[str]] = defaultdict(list)
    for p in persons:
        by_year[p.birth_date.year].append(p.person_id)

    def take_from_years(lo: int, hi: int, sex: str | None) -> Person | None:
        years = list(range(lo, hi + 1))
        g.shuffle(years)
        for y in years:
            ids = [i for i in by_year.get(y, []) if i in free]
            if sex is not None:
                ids = [i for i in ids if by_id[i].sex == sex]
            if ids:
                pid = ids[int(g.integers(0, len(ids)))]
                free.discard(pid)
                return by_id[pid]
        return None

    origins = list(ORIGIN_SHARE)
    origin_p = np.array([ORIGIN_SHARE[o] for o in origins])
    fathers_by_origin: dict[OriginGroup, list[Person]] = defaultdict(list)
    hh = 0
    ref = REFERENCE_DATE
    for p in persons:
        if p.person_id not in free or p.sex != "M" or not 24 <= p.age_on(ref) <= 75:
            continue
        if g.random() >= HOUSEHOLD_FATHER_SHARE:
            continue
        free.discard(p.person_id)
        hh += 1
        fam_id = f"H{hh:05d}"
        origin = origins[int(g.choice(len(origins), p=origin_p))]
        p.origin, p.role, p.family_id = origin, "father", fam_id
        p.nationality = _choice(g, NATIONALITY[origin])
        brothers = fathers_by_origin[origin]
        if origin in ARAB_ORIGINS and brothers and g.random() < CLAN_SHARE:
            brother = brothers[int(g.integers(0, len(brothers)))]
            p.family, p.father_given = brother.family, brother.father_given
            p.grandfather_given, p.clan_id = brother.grandfather_given, brother.clan_id
            p.nationality = brother.nationality
        else:
            p.family = namer.family(origin)
            p.father_given = namer.given(origin, "M")
            p.grandfather_given = namer.given(origin, "M")
            p.clan_id = f"C{hh:05d}"
        assert p.family is not None
        p.given = namer.safe_given(origin, "M", p.family)
        p.birth_family = p.family
        fathers_by_origin[origin].append(p)
        fy = p.birth_date.year
        mother = None
        if g.random() < MOTHER_SHARE:
            mother = take_from_years(fy - 3, fy + 12, "F")
            if mother is not None and mother.age_on(ref) < 19:
                free.add(mother.person_id)
                mother = None
        if mother is not None:
            mother.origin, mother.role, mother.family_id = origin, "mother", fam_id
            mother.clan_id = f"M{hh:05d}"
            mother.nationality = p.nationality
            mother.birth_family = namer.family(origin)
            mother.family = p.family if origin in WIFE_TAKES_HUSBAND_NAME else mother.birth_family
            mother.given = namer.safe_given(origin, "F", mother.family)
            mother.father_given = namer.given(origin, "M")
            mother.grandfather_given = namer.given(origin, "M")
        k = int(g.poisson(MEAN_CHILDREN.get(origin, 1.8)))
        young = (mother or p).birth_date.year
        children: list[Person] = []
        for _ in range(k):
            child = take_from_years(young + 19, min(young + 44, ref.year), None)
            if child is None:
                break
            child.origin, child.role, child.family_id = origin, "child", fam_id
            child.clan_id, child.nationality = p.clan_id, p.nationality
            child.family = child.birth_family = p.family
            child.father_given, child.grandfather_given = p.given, p.father_given
            child.given = namer.safe_given(origin, child.sex, p.family)
            child.father_id = p.person_id
            child.mother_id = mother.person_id if mother else None
            children.append(child)
        sons = [c for c in children if c.sex == "M"]
        if sons and g.random() < SAME_NAME_SON_SHARE:
            son = sons[0]
            son.given = p.given
            son.flags.append("same_name_as_father")
        if len(children) >= 2 and g.random() < TWIN_SHARE:
            a, b = children[0], children[1]
            b.birth_date = a.birth_date
            a.twin_group = b.twin_group = f"T{hh:05d}"
            if a.given == b.given:
                b.given = namer.safe_given(origin, b.sex, p.family)
    # Everyone left is a one person household.
    for p in persons:
        if p.person_id not in free:
            continue
        free.discard(p.person_id)
        hh += 1
        origin = origins[int(g.choice(len(origins), p=origin_p))]
        p.origin, p.role, p.family_id, p.clan_id = origin, "single", f"H{hh:05d}", f"C{hh:05d}"
        p.nationality = _choice(g, NATIONALITY[origin])
        p.family = p.birth_family = namer.family(origin)
        p.given = namer.safe_given(origin, p.sex, p.family)
        p.father_given = namer.given(origin, "M")
        p.grandfather_given = namer.given(origin, "M")
    _assign_identifiers(persons, g)
    return People(persons, by_id, seed)


def _assign_identifiers(persons: list[Person], g: np.random.Generator) -> None:
    used: set[str] = set()
    areas: dict[str, str] = {}
    phones: dict[str, str] = {}
    for p in persons:
        if p.nationality == "ARE":
            p.eid = _eid(g, p.birth_date, used)
        elif p.nationality in GCC_NON_UAE:
            p.gcc_id = _gcc(g, used)
            if g.random() < GCC_WITH_EID_SHARE:
                p.eid = _eid(g, p.birth_date, used)
        else:
            p.passport = _passport(g, used)
            if g.random() >= VISITOR_SHARE:
                p.eid = _eid(g, p.birth_date, used)
            else:
                p.flags.append("visitor")
        if p.family_id not in areas:
            areas[p.family_id] = f"A{int(g.integers(1, 41)):02d}"
        p.area = areas[p.family_id]
        if p.role in ("father", "mother", "single"):
            p.phone = _phone(g)
            if p.role == "father":
                phones[p.family_id] = p.phone
    for p in persons:
        if p.role == "child":
            shared = phones.get(p.family_id)
            if shared and (p.age_on(REFERENCE_DATE) < 16 or g.random() < CHILD_SHARES_PHONE):
                p.phone = shared
            else:
                p.phone = _phone(g)
    for p in persons:
        if p.mother_id and p.age_on(REFERENCE_DATE) < 1.0:
            p.flags.append("newborn")
