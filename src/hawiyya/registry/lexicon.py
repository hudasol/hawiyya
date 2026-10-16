"""Name lexicon loading and denylist enforcement.

The lexicon is a generator input (L1). It is never read by L2 to L5: the matcher must not
know which spellings the generator considers equivalent.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from hawiyya.contract.enums import OriginGroup
from hawiyya.core.paths import DATA

ORIGIN_CODES: dict[str, OriginGroup] = {
    "G": OriginGroup.GULF_ARAB,
    "A": OriginGroup.OTHER_ARAB,
    "S": OriginGroup.SOUTH_ASIAN,
    "E": OriginGroup.SOUTHEAST_ASIAN,
    "W": OriginGroup.WESTERN,
}
TIER_WEIGHT = {1: 10.0, 2: 3.0, 3: 1.0}


@dataclass(frozen=True)
class NameEntry:
    ar: str
    latin: tuple[str, ...]
    origins: tuple[OriginGroup, ...]
    tier: int
    sex: str | None = None

    @property
    def canonical_latin(self) -> str:
        return self.latin[0]


@dataclass(frozen=True)
class Lexicon:
    author: str
    given: tuple[NameEntry, ...]
    family: tuple[NameEntry, ...]
    source_path: str

    def given_for(self, origin: OriginGroup, sex: str) -> list[NameEntry]:
        return [g for g in self.given if origin in g.origins and g.sex == sex]

    def family_for(self, origin: OriginGroup) -> list[NameEntry]:
        return [f for f in self.family if origin in f.origins]


@dataclass(frozen=True)
class Denylist:
    family_latin: frozenset[str]
    family_ar: frozenset[str]
    combinations: frozenset[tuple[str, str]]

    def family_denied(self, entry: NameEntry) -> bool:
        latin = {_fold(x) for x in entry.latin}
        return bool(latin & {_fold(x) for x in self.family_latin}) or entry.ar in self.family_ar

    def combination_denied(self, given: NameEntry, family: NameEntry) -> bool:
        gl = {_fold(x) for x in given.latin}
        fl = {_fold(x) for x in family.latin}
        return any(_fold(g) in gl and _fold(f) in fl for g, f in self.combinations)


def _fold(s: str) -> str:
    return "".join(ch for ch in s.lower() if ch.isalnum())


def _entry(raw: dict[str, object]) -> NameEntry:
    origins = tuple(ORIGIN_CODES[c] for c in str(raw["origins"]))
    latin = raw["latin"]
    assert isinstance(latin, list)
    tier = raw["tier"]
    assert isinstance(tier, int)
    sex = raw.get("sex")
    return NameEntry(
        ar=str(raw["ar"]),
        latin=tuple(str(x) for x in latin),
        origins=origins,
        tier=tier,
        sex=str(sex) if sex is not None else None,
    )


def load_lexicon(path: Path | None = None) -> Lexicon:
    p = path or DATA / "lexicon" / "names.json"
    raw = json.loads(p.read_text(encoding="utf-8"))
    lex = Lexicon(
        author=str(raw["author"]),
        given=tuple(_entry(g) for g in raw["given"]),
        family=tuple(_entry(f) for f in raw["family"]),
        source_path=p.as_posix(),
    )
    deny = load_denylist()
    bad = [f.canonical_latin for f in lex.family if deny.family_denied(f)]
    if bad:
        raise ValueError(f"lexicon contains denylisted family names: {bad}")
    return lex


@lru_cache(maxsize=1)
def load_denylist(path: Path | None = None) -> Denylist:
    p = path or DATA / "lexicon" / "denylist.json"
    raw = json.loads(p.read_text(encoding="utf-8"))
    return Denylist(
        family_latin=frozenset(raw["family_names_latin"]),
        family_ar=frozenset(raw["family_names_ar"]),
        combinations=frozenset((a, b) for a, b in raw["full_name_combinations"]),
    )


@lru_cache(maxsize=4)
def default_lexicon() -> Lexicon:
    return load_lexicon()
