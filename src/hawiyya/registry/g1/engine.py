"""G1 corruption engine: renders registration records for a person at a facility.

Name rendering styles: formal Arabic, card Latin, lexicon spelling variants, Gulf style
transliteration and Arabizi, followed by token drops, order swaps, initials, typos and
honorifics. Dates of birth, sex, identifiers and contact fields are corrupted at rates that
are parameters with provenance ASSUMPTION. No claim of realism is made.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np

from hawiyya.contract.enums import DatePrecision, IdCapture, IdKind, OriginGroup, Sex
from hawiyya.registry.facilities import (
    PLACEHOLDER_VALUES,
    SANCTIONED_FLAGGED_SHARE,
    SANCTIONED_PLACEHOLDER,
    Facility,
)
from hawiyya.registry.g1.translit import translit_name
from hawiyya.registry.lexicon import NameEntry
from hawiyya.registry.people import ARAB_ORIGINS, People, Person

WINDOW_START = date(2023, 1, 1)
WINDOW_END = date(2026, 9, 30)
NEWBORN_DAYS = 90


@dataclass(frozen=True)
class G1Config:
    """Corruption rates (ASSUMPTION). Name rates are scaled by the facility noise factor."""

    drop_grandfather: float = 0.5
    drop_father: float = 0.10
    swap_order: float = 0.04
    father_initial: float = 0.04
    latin_typo: float = 0.06
    arabic_typo: float = 0.03
    honorific: float = 0.03
    all_caps: float = 0.20
    bin_prefix: float = 0.12
    dob_transpose: float = 0.015
    dob_digit: float = 0.01
    dob_year_off: float = 0.01
    dob_missing: float = 0.02
    dob_year_only: float = 0.01
    sex_flip: float = 0.01
    sex_missing: float = 0.02
    phone_missing: float = 0.30
    nationality_missing: float = 0.10
    area_missing: float = 0.15
    placeholder_override: float | None = None


@dataclass(frozen=True)
class Rendered:
    fields: dict[str, object]
    name_style: str
    log: tuple[str, ...]


def name_entries(p: Person, g: np.random.Generator, cfg: G1Config) -> list[NameEntry]:
    """The name tokens a registration of this person would carry, before rendering."""
    assert p.given is not None and p.family is not None
    toks: list[NameEntry] = [p.given]
    if p.origin == OriginGroup.GULF_ARAB:
        assert p.father_given is not None
        toks.append(p.father_given)
        if p.grandfather_given is not None and g.random() >= cfg.drop_grandfather:
            toks.append(p.grandfather_given)
    elif p.origin == OriginGroup.OTHER_ARAB:
        assert p.father_given is not None
        toks.append(p.father_given)
    toks.append(p.family)
    return toks


def _latin_tokens(entries: list[NameEntry], style: str, p: Person, g: np.random.Generator) -> list[str]:
    if style in ("gulf", "arabizi") and p.origin in ARAB_ORIGINS:
        text = " ".join(e.ar for e in entries)
        out = translit_name(text, g, "gulf" if style == "gulf" else "arabizi").split()
        return [t.lower() for t in out] if style == "arabizi" else out
    if style == "card":
        toks = [e.canonical_latin for e in entries]
    else:
        toks = [e.latin[int(g.integers(0, len(e.latin)))] for e in entries]
    if style == "arabizi":  # non Arab names typed casually in an app
        toks = [t.lower() for t in toks]
    return " ".join(toks).split()


def _typo_latin(tok: str, g: np.random.Generator) -> str:
    if len(tok) < 3:
        return tok
    i = int(g.integers(1, len(tok) - 1))
    op = int(g.integers(0, 3))
    letters = "aeiouhnrstlmkd"
    if op == 0:
        return tok[:i] + tok[i + 1 :]
    if op == 1:
        return tok[:i] + letters[int(g.integers(0, len(letters)))] + tok[i:]
    return tok[: i - 1] + tok[i] + tok[i - 1] + tok[i + 1 :]


def _typo_arabic(tok: str, g: np.random.Generator) -> str:
    if len(tok) < 3:
        return tok
    i = int(g.integers(1, len(tok) - 1))
    if g.random() < 0.5:
        return tok[:i] + tok[i + 1 :]
    return tok[: i - 1] + tok[i] + tok[i - 1] + tok[i + 1 :]


def render_names(p: Person, fac: Facility, g: np.random.Generator, cfg: G1Config,
                 log: list[str]) -> tuple[str | None, str | None, str]:
    entries = name_entries(p, g, cfg)
    noise = fac.noise
    if len(entries) >= 3 and g.random() < cfg.drop_father * noise:
        entries = [entries[0], *entries[2:]]
        log.append("name:drop_father")
    name_ar = name_latin = None
    style = fac.latin_style
    if "ar" in fac.scripts:
        toks = [e.ar for e in entries]
        if p.origin == OriginGroup.GULF_ARAB and len(toks) >= 3 and g.random() < cfg.bin_prefix:
            toks.insert(1, "بن" if p.sex == "M" else "بنت")
            log.append("name:bin")
        if g.random() < cfg.arabic_typo * noise:
            j = int(g.integers(0, len(toks)))
            toks[j] = _typo_arabic(toks[j], g)
            log.append("name:ar_typo")
        if g.random() < cfg.swap_order * noise:
            toks = [toks[-1], *toks[:-1]]
            log.append("name:ar_swap")
        name_ar = " ".join(toks)
    if "latin" in fac.scripts:
        if style == "variant" and p.origin in ARAB_ORIGINS and g.random() < 0.3:
            style = "formal_translit"
            text = " ".join(e.ar for e in entries)
            toks = translit_name(text, g, "formal").split()
        else:
            toks = _latin_tokens(entries, style, p, g)
        if p.origin == OriginGroup.GULF_ARAB and len(toks) >= 3 and g.random() < cfg.bin_prefix:
            toks.insert(1, "bin" if p.sex == "M" else "bint")
            log.append("name:bin")
        if len(toks) >= 3 and g.random() < cfg.father_initial * noise:
            toks[1] = toks[1][0].upper() + "."
            log.append("name:initial")
        if g.random() < cfg.latin_typo * noise:
            j = int(g.integers(0, len(toks)))
            toks[j] = _typo_latin(toks[j], g)
            log.append("name:typo")
        if g.random() < cfg.swap_order * noise:
            # Move the family name (with a separate article, as in "Al Masri") to the front.
            k = 2 if len(toks) >= 3 and toks[-2].lower() in ("al", "el") else 1
            toks = [*toks[-k:], *toks[:-k]]
            log.append("name:swap")
        if g.random() < cfg.honorific * noise:
            hon = ["Mr", "Dr"] if p.sex == "M" else ["Mrs", "Ms", "Dr"]
            if p.origin == OriginGroup.GULF_ARAB and p.sex == "M":
                hon.append("Sheikh")
            toks.insert(0, hon[int(g.integers(0, len(hon)))])
            log.append("name:honorific")
        name_latin = " ".join(toks)
        if style in ("card", "variant", "formal_translit") and g.random() < cfg.all_caps:
            name_latin = name_latin.upper()
    if name_ar is not None and name_latin is not None:
        name_style = "bilingual_card"
    elif name_ar is not None:
        name_style = "formal_ar"
    else:
        name_style = {"card": "formal_en", "variant": "variant_en", "gulf": "gulf",
                      "arabizi": "arabizi", "formal_translit": "formal_translit"}[style]  # fmt: skip
    return name_ar, name_latin, name_style


def _corrupt_dob(birth: date, fac: Facility, g: np.random.Generator, cfg: G1Config,
                 log: list[str]) -> tuple[str | None, DatePrecision | None]:
    r = g.random()
    acc = cfg.dob_missing
    if r < acc:
        log.append("dob:missing")
        return None, None
    acc += fac.dob_default_rate
    if r < acc:
        log.append("dob:default_jan1")
        return date(birth.year, 1, 1).isoformat(), DatePrecision.DAY
    acc += cfg.dob_year_only
    if r < acc:
        log.append("dob:year_only")
        return date(birth.year, 1, 1).isoformat(), DatePrecision.YEAR
    acc += cfg.dob_transpose
    if r < acc and birth.day <= 12 and birth.day != birth.month:
        log.append("dob:transpose")
        return date(birth.year, birth.day, birth.month).isoformat(), DatePrecision.DAY
    acc += cfg.dob_digit
    if r < acc:
        s = birth.isoformat()
        for _ in range(10):
            pos = [2, 3, 6, 9][int(g.integers(0, 4))]
            cand = s[:pos] + str(int(g.integers(0, 10))) + s[pos + 1 :]
            try:
                if cand != s and date.fromisoformat(cand):
                    log.append("dob:digit")
                    return cand, DatePrecision.DAY
            except ValueError:
                continue
    acc += cfg.dob_year_off
    if r < acc:
        d = 1 if g.random() < 0.5 else -1
        try:
            log.append("dob:year_off")
            return birth.replace(year=birth.year + d).isoformat(), DatePrecision.DAY
        except ValueError:
            pass
    return birth.isoformat(), DatePrecision.DAY


def _typo_digits(v: str, g: np.random.Generator) -> str:
    i = int(g.integers(3, len(v) - 1))
    if g.random() < 0.5:
        digit = str((int(v[i]) + int(g.integers(1, 10))) % 10)
        return v[:i] + digit + v[i + 1 :]
    return v[:i] + v[i + 1] + v[i] + v[i + 2 :]


def _placeholder(g: np.random.Generator) -> str:
    vals = [v for v, _ in PLACEHOLDER_VALUES]
    p = np.array([w for _, w in PLACEHOLDER_VALUES])
    return vals[int(g.choice(len(vals), p=p / p.sum()))]


def render_identifier(p: Person, people: People, fac: Facility, reg: date,
                      g: np.random.Generator, cfg: G1Config, log: list[str],
                      file_no: str) -> tuple[str | None, IdKind | None, IdCapture | None]:
    mother = people.by_id.get(p.mother_id) if p.mother_id else None
    if (reg - p.birth_date).days < NEWBORN_DAYS and mother is not None and mother.eid:
        log.append("id:mother_substitute")
        return mother.eid, IdKind.MOTHER_EID, IdCapture.SUBSTITUTE
    rate = fac.placeholder_rate if cfg.placeholder_override is None else cfg.placeholder_override
    if g.random() < rate:
        log.append("id:placeholder")
        value = _placeholder(g)
        if value == SANCTIONED_PLACEHOLDER and g.random() < SANCTIONED_FLAGGED_SHARE:
            return value, IdKind.PLACEHOLDER, IdCapture.PLACEHOLDER
        return value, IdKind.EID, IdCapture.MANUAL
    if p.eid:
        if g.random() < fac.reader_share:
            return p.eid, IdKind.EID, IdCapture.READER
        if g.random() < fac.id_typo_rate:
            log.append("id:typo")
            return _typo_digits(p.eid, g), IdKind.EID, IdCapture.MANUAL
        return p.eid, IdKind.EID, IdCapture.MANUAL
    if p.gcc_id:
        return p.gcc_id, IdKind.GCC_ID, IdCapture.MANUAL
    if p.passport and g.random() < 0.6:
        v = p.passport
        if g.random() < fac.id_typo_rate:
            log.append("id:typo")
            v = v[:2] + _typo_digits(v[2:], g)
        return v, IdKind.PASSPORT, IdCapture.MANUAL
    log.append("id:file_no")
    return file_no, IdKind.FILE_NO, IdCapture.SUBSTITUTE


def render_record(p: Person, people: People, fac: Facility, reg: date, g: np.random.Generator,
                  cfg: G1Config, file_no: str) -> Rendered:
    log: list[str] = []
    name_ar, name_latin, name_style = render_names(p, fac, g, cfg, log)
    dob, precision = _corrupt_dob(p.birth_date, fac, g, cfg, log)
    sex: Sex | None = Sex(p.sex)
    r = g.random()
    if r < cfg.sex_missing:
        sex = None
        log.append("sex:missing")
    elif r < cfg.sex_missing + cfg.sex_flip:
        sex = Sex.FEMALE if p.sex == "M" else Sex.MALE
        log.append("sex:flip")
    id_value, id_kind, id_capture = render_identifier(p, people, fac, reg, g, cfg, log, file_no)
    phone = p.phone if g.random() >= cfg.phone_missing or fac.style == "mobile_app" else None
    nationality = p.nationality if g.random() >= cfg.nationality_missing else None
    area = p.area if g.random() >= cfg.area_missing else None
    fields: dict[str, object] = dict(
        facility_id=fac.facility_id, name_ar=name_ar, name_latin=name_latin, sex=sex,
        dob=dob, dob_precision=precision, id_value=id_value, id_kind=id_kind,
        id_capture=id_capture, nationality=nationality, phone=phone, area=area,
        registered_on=reg.isoformat(),
    )  # fmt: skip
    return Rendered(fields, name_style, tuple(log))


def registration_date(p: Person, g: np.random.Generator, first: bool) -> date:
    start = max(WINDOW_START, p.birth_date)
    if first and "newborn" in p.flags:
        return p.birth_date + timedelta(days=int(g.integers(0, 60)))
    span = (WINDOW_END - start).days
    return start + timedelta(days=int(g.integers(0, max(span, 1))))
