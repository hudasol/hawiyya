"""G2: an independent registration generator.

G2 renders names from the Arabic forms with its own conventions and adds heavier noise than G1.
It must not import ``hawiyya.normalise``, ``hawiyya.registry.g1`` or any ported Tahdeed code (an
import contract enforces this). Differences from G1, on purpose:

- Romanisation tables written separately, mixing an academic convention (hyphenated articles,
  sun letter assimilation, apostrophes for ayn and hamza), a Maghrebi French convention (ou,
  ch, dj, e) and a Levantine chat convention for Arabizi (2 for qaf, S and T for emphatics,
  3' for ghayn, no 9, 6 or 8).
- Keyboard adjacent typos in both scripts, OCR style confusions, truncated family names,
  honorifics, swapped given and family order, married women registered under the husband's
  family name, mixed script entries, doubled spaces and zero width characters.
- Its own date, sex and identifier errors, including two digit identifier typos and a mid
  month default date.

All rates are ASSUMPTION values chosen by the author. G2 shares the people (households, twins,
identifiers) with G1 so the comparison isolates the rendering.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

import numpy as np

from hawiyya.contract.enums import DatePrecision, IdCapture, IdKind, OriginGroup, Sex
from hawiyya.registry.facilities import PLACEHOLDER_VALUES, SANCTIONED_PLACEHOLDER, Facility
from hawiyya.registry.lexicon import NameEntry
from hawiyya.registry.people import People, Person
from hawiyya.registry.rendered import Rendered

ARAB = {OriginGroup.GULF_ARAB, OriginGroup.OTHER_ARAB}
AL = "ال"
ABD = "عبد"

# Arabic letter -> {convention: options}. Conventions: acad, magh, chat.
TABLE: dict[str, dict[str, tuple[str, ...]]] = {
    "ب": {"*": ("b",)},
    "ت": {"*": ("t",)},
    "ث": {"acad": ("th",), "magh": ("t", "th"), "chat": ("th", "s")},
    "ج": {"acad": ("j",), "magh": ("dj", "j"), "chat": ("j", "g")},
    "ح": {"acad": ("h",), "magh": ("h",), "chat": ("7",)},
    "خ": {"acad": ("kh",), "magh": ("kh", "x"), "chat": ("7'", "kh", "5")},
    "د": {"*": ("d",)},
    "ذ": {"acad": ("dh",), "magh": ("d", "dh"), "chat": ("z", "th")},
    "ر": {"*": ("r",)},
    "ز": {"*": ("z",)},
    "س": {"acad": ("s",), "magh": ("ss", "s"), "chat": ("s",)},
    "ش": {"acad": ("sh",), "magh": ("ch",), "chat": ("sh", "ch")},
    "ص": {"acad": ("s",), "magh": ("ss", "s"), "chat": ("S", "s")},
    "ض": {"acad": ("d",), "magh": ("dh", "d"), "chat": ("D", "d")},
    "ط": {"acad": ("t",), "magh": ("t", "tt"), "chat": ("T", "t")},
    "ظ": {"acad": ("z",), "magh": ("dh", "z"), "chat": ("Z", "z")},
    "ع": {"acad": ("'", ""), "magh": ("a", "e", ""), "chat": ("3", "e")},
    "غ": {"acad": ("gh",), "magh": ("gh", "r"), "chat": ("3'", "gh")},
    "ف": {"*": ("f",)},
    "ق": {"acad": ("q",), "magh": ("k", "q"), "chat": ("2", "q", "g")},
    "ك": {"acad": ("k",), "magh": ("k",), "chat": ("k",)},
    "ل": {"*": ("l",)},
    "م": {"*": ("m",)},
    "ن": {"*": ("n",)},
    "ه": {"*": ("h", "")},
    "ء": {"acad": ("'",), "magh": ("",), "chat": ("2", "")},
    "أ": {"*": ("a", "'a")},
    "إ": {"*": ("i", "e")},
    "آ": {"*": ("aa", "a")},
    "ؤ": {"*": ("ou", "o")},
    "ئ": {"*": ("i", "y", "e")},
    "ة": {"acad": ("a", "ah"), "magh": ("a", "e"), "chat": ("a", "e")},
}  # fmt: skip
LONG = {
    "ا": ("a", "aa", "e"),
    "و": ("u", "ou", "o", "oo"),
    "ي": ("i", "ee", "ei", "y"),
    "ى": ("a", "i", "y"),
}
VOWELS = (("a", 0.45), ("e", 0.25), ("i", 0.15), ("ou", 0.10), ("o", 0.05))
SUN = set("تثدذرزسشصضطظلن")
QWERTY = ["qwertyuiop", "asdfghjkl", "zxcvbnm"]
AR_KEYS = ["ضصثقفغعهخحج",
           "شسيبلاتنمكط",
           "ئءؤرلىةوزظ"]  # fmt: skip
OCR = (("rn", "m"), ("m", "rn"), ("l", "1"), ("o", "0"), ("cl", "d"), ("i", "l"))
HONORIFICS = ("Mr.", "Mrs.", "Dr.", "Sh.", "Ms.")
ZWSP = "​"


@dataclass(frozen=True)
class G2Config:
    keyboard_typo: float = 0.08
    ocr: float = 0.03
    truncate_family: float = 0.03
    honorific: float = 0.05
    swap: float = 0.08
    married_name: float = 0.3
    mixed_script: float = 0.03
    double_space: float = 0.10
    zero_width: float = 0.05
    upper: float = 0.20
    drop_father: float = 0.15
    keep_grandfather: float = 0.4
    dob_transpose: float = 0.03
    dob_digit: float = 0.02
    dob_year_off: float = 0.015
    dob_mid_month: float = 0.01
    dob_missing: float = 0.03
    sex_flip: float = 0.015
    sex_missing: float = 0.03
    id_two_digit_share: float = 0.3
    phone_missing: float = 0.35
    placeholder_override: float | None = None


def _pick(g: np.random.Generator, opts: tuple[str, ...]) -> str:
    return opts[int(g.integers(0, len(opts)))]


def _vowel(g: np.random.Generator) -> str:
    r = g.random()
    acc = 0.0
    for v, w in VOWELS:
        acc += w
        if r < acc:
            return v
    return "a"


def romanise_word(w: str, conv: str, g: np.random.Generator) -> str:
    out: list[str] = []
    after_consonant = False
    for i, ch in enumerate(w):
        if ch in LONG:
            opts = LONG[ch]
            if i == 0 and ch == "و":
                opts = ("w", "ou") if conv == "magh" else ("w",)
            elif i == 0 and ch == "ي":
                opts = ("y", "i")
            out.append(_pick(g, opts))
            after_consonant = False
            continue
        table = TABLE.get(ch)
        if table is None:
            continue
        s = _pick(g, table.get(conv) or table["*"])
        if after_consonant and s and g.random() < 0.7:
            out.append(_vowel(g))
        out.append(s)
        after_consonant = bool(s) and s[-1].isalpha()
    return "".join(out)


def romanise_name(text: str, conv: str, g: np.random.Generator) -> str:
    words: list[str] = []
    for w in text.split():
        if w.startswith(ABD) and len(w) > 3:
            rest = w[3:]
            if rest.startswith(AL):
                rest = rest[2:]
            body = romanise_word(rest, conv, g)
            head = _pick(g, ("Abd al-", "Abdel-", "Abdu", "Abd ul ", "Abd el "))
            words.append(head + body)
        elif w.startswith(AL) and len(w) > 3:
            base = w[2:]
            body = romanise_word(base, conv, g)
            if conv == "acad" and base[0] in SUN and g.random() < 0.4 and body:
                words.append(f"a{body[0]}-{body}")
            else:
                art = _pick(g, ("al-", "el-", "Al ", "El ")) if conv != "chat" else "el "
                words.append(art + body)
        else:
            words.append(romanise_word(w, conv, g))
    s = " ".join(x for x in words if x)
    if conv != "chat":
        s = " ".join(t[:1].upper() + t[1:] for t in s.split(" "))
    return s


def _keyboard_typo(s: str, g: np.random.Generator, rows: list[str]) -> str:
    idx = [i for i, ch in enumerate(s) if any(ch.lower() in r for r in rows)]
    if not idx:
        return s
    i = idx[int(g.integers(0, len(idx)))]
    ch = s[i].lower()
    for r in rows:
        if ch in r:
            j = r.index(ch)
            nb = [r[k] for k in (j - 1, j + 1) if 0 <= k < len(r)]
            rep = nb[int(g.integers(0, len(nb)))]
            return s[:i] + (rep.upper() if s[i].isupper() else rep) + s[i + 1:]
    return s


def _ocr(s: str, g: np.random.Generator) -> str:
    cands = [(a, b) for a, b in OCR if a in s]
    if not cands:
        return s
    a, b = cands[int(g.integers(0, len(cands)))]
    return s.replace(a, b, 1)


def _entries(p: Person, people: People, g: np.random.Generator,
             cfg: G2Config) -> tuple[list[NameEntry], bool]:
    assert p.given is not None and p.family is not None
    family = p.family
    married = False
    if p.role == "mother" and p.origin in ARAB and g.random() < cfg.married_name:
        husband = next((q for q in people.persons if q.family_id == p.family_id
                        and q.role == "father"), None)  # fmt: skip
        if husband is not None and husband.family is not None:
            family, married = husband.family, True
    toks = [p.given]
    if p.origin in ARAB and p.father_given is not None and g.random() >= cfg.drop_father:
        toks.append(p.father_given)
        if (p.origin == OriginGroup.GULF_ARAB and p.grandfather_given is not None
                and g.random() < cfg.keep_grandfather):  # fmt: skip
            toks.append(p.grandfather_given)
    toks.append(family)
    return toks, married


def _latin(entries: list[NameEntry], p: Person, conv: str, g: np.random.Generator) -> str:
    if p.origin in ARAB:
        return romanise_name(" ".join(e.ar for e in entries), conv, g)
    text = " ".join(e.canonical_latin for e in entries)
    return text.lower() if conv == "chat" else text


def render_names(p: Person, people: People, fac: Facility, g: np.random.Generator,
                 cfg: G2Config, log: list[str]) -> tuple[str | None, str | None, str]:
    entries, married = _entries(p, people, g, cfg)
    if married:
        log.append("name:married")
    noise = fac.noise
    conv = {"card": "acad", "variant": "magh", "gulf": "magh", "arabizi": "chat"}[fac.latin_style]
    if fac.latin_style == "variant" and g.random() < 0.5:
        conv = "acad"
    name_ar = name_latin = None
    if "ar" in fac.scripts:
        toks = [e.ar for e in entries]
        if g.random() < cfg.keyboard_typo * noise:
            j = int(g.integers(0, len(toks)))
            toks[j] = _keyboard_typo(toks[j], g, AR_KEYS)
            log.append("name:ar_keyboard")
        name_ar = " ".join(toks)
    if "latin" in fac.scripts:
        s = _latin(entries, p, conv, g)
        toks = s.split(" ")
        if len(toks) >= 2 and g.random() < cfg.swap * noise:
            toks = [toks[-1], *toks[:-1]]
            log.append("name:swap")
        if len(toks) >= 2 and g.random() < cfg.truncate_family * noise and len(toks[-1]) > 5:
            toks[-1] = toks[-1][:4] + "."
            log.append("name:truncate")
        s = " ".join(toks)
        if g.random() < cfg.keyboard_typo * noise:
            s = _keyboard_typo(s, g, QWERTY)
            log.append("name:keyboard")
        if g.random() < cfg.ocr * noise:
            s = _ocr(s, g)
            log.append("name:ocr")
        if g.random() < cfg.honorific * noise:
            s = HONORIFICS[int(g.integers(0, len(HONORIFICS)))] + " " + s
            log.append("name:honorific")
        if p.origin in ARAB and g.random() < cfg.mixed_script:
            s = s + " " + entries[-1].ar
            log.append("name:mixed_script")
        if g.random() < cfg.double_space:
            s = s.replace(" ", "  ", 1)
        if g.random() < cfg.zero_width:
            k = int(g.integers(1, max(2, len(s))))
            s = s[:k] + ZWSP + s[k:]
        if conv != "chat" and g.random() < cfg.upper:
            s = s.upper()
        name_latin = s
    style = "g2_" + ("ar" if name_latin is None else conv if name_ar is None else "bilingual")
    return name_ar, name_latin, style


def _dob(p: Person, fac: Facility, g: np.random.Generator, cfg: G2Config,
         log: list[str]) -> tuple[str | None, DatePrecision | None]:
    b = p.birth_date
    r = g.random()
    if r < cfg.dob_missing:
        log.append("dob:missing")
        return None, None
    r -= cfg.dob_missing
    if r < fac.dob_default_rate * 1.5:
        log.append("dob:default_jan1")
        return date(b.year, 1, 1).isoformat(), DatePrecision.DAY
    r -= fac.dob_default_rate * 1.5
    if r < cfg.dob_mid_month:
        log.append("dob:mid_month")
        return date(b.year, b.month, 15).isoformat(), DatePrecision.DAY
    r -= cfg.dob_mid_month
    if r < cfg.dob_transpose and b.day <= 12 and b.day != b.month:
        log.append("dob:transpose")
        return date(b.year, b.day, b.month).isoformat(), DatePrecision.DAY
    r -= cfg.dob_transpose
    if r < cfg.dob_digit:
        day = min(28, max(1, b.day + int(g.choice([-10, 10, -1, 1]))))
        log.append("dob:digit")
        return date(b.year, b.month, day).isoformat(), DatePrecision.DAY
    r -= cfg.dob_digit
    if r < cfg.dob_year_off:
        log.append("dob:year_off")
        y = b.year + int(g.choice([-1, 1]))
        return date(y, b.month, min(b.day, 28)).isoformat(), DatePrecision.DAY
    return b.isoformat(), DatePrecision.DAY


def _id_typo(v: str, g: np.random.Generator, cfg: G2Config) -> str:
    n = 2 if g.random() < cfg.id_two_digit_share else 1
    chars = list(v)
    for _ in range(n):
        i = int(g.integers(3, len(chars)))
        if chars[i].isdigit():
            chars[i] = str((int(chars[i]) + int(g.integers(1, 10))) % 10)
    return "".join(chars)


def _identifier(p: Person, people: People, fac: Facility, reg: date, g: np.random.Generator,
                cfg: G2Config, log: list[str],
                file_no: str) -> tuple[str | None, IdKind | None, IdCapture | None]:
    mother = people.by_id.get(p.mother_id) if p.mother_id else None
    if (reg - p.birth_date).days < 90 and mother is not None and mother.eid:
        log.append("id:mother_substitute")
        return mother.eid, IdKind.MOTHER_EID, IdCapture.SUBSTITUTE
    rate = fac.placeholder_rate if cfg.placeholder_override is None else cfg.placeholder_override
    if g.random() < rate:
        log.append("id:placeholder")
        vals = [v for v, _ in PLACEHOLDER_VALUES]
        w = np.array([x for _, x in PLACEHOLDER_VALUES])
        value = vals[int(g.choice(len(vals), p=w / w.sum()))]
        if value == SANCTIONED_PLACEHOLDER and g.random() < 0.5:
            return value, IdKind.PLACEHOLDER, IdCapture.PLACEHOLDER
        return value, IdKind.EID, IdCapture.MANUAL
    if p.eid:
        if g.random() < fac.reader_share:
            return p.eid, IdKind.EID, IdCapture.READER
        if g.random() < fac.id_typo_rate * 1.5:
            log.append("id:typo")
            return _id_typo(p.eid, g, cfg), IdKind.EID, IdCapture.MANUAL
        return p.eid, IdKind.EID, IdCapture.MANUAL
    if p.gcc_id:
        return p.gcc_id, IdKind.GCC_ID, IdCapture.MANUAL
    if p.passport and g.random() < 0.5:
        return p.passport, IdKind.PASSPORT, IdCapture.MANUAL
    log.append("id:file_no")
    return file_no, IdKind.FILE_NO, IdCapture.SUBSTITUTE


def _phone(p: Person, g: np.random.Generator, cfg: G2Config) -> str | None:
    if p.phone is None or g.random() < cfg.phone_missing:
        return None
    v = p.phone
    style = int(g.integers(0, 3))
    if style == 1:
        return "+971 " + v[1:3] + " " + v[3:6] + " " + v[6:]
    if style == 2:
        return v[:3] + "-" + v[3:]
    return v


def render_record_g2(p: Person, people: People, fac: Facility, reg: date,
                     g: np.random.Generator, cfg: G2Config, file_no: str) -> Rendered:
    log: list[str] = []
    name_ar, name_latin, style = render_names(p, people, fac, g, cfg, log)
    dob, precision = _dob(p, fac, g, cfg, log)
    sex: Sex | None = Sex(p.sex)
    r = g.random()
    if r < cfg.sex_missing:
        sex = None
        log.append("sex:missing")
    elif r < cfg.sex_missing + cfg.sex_flip:
        sex = Sex.FEMALE if p.sex == "M" else Sex.MALE
        log.append("sex:flip")
    id_value, id_kind, id_capture = _identifier(p, people, fac, reg, g, cfg, log, file_no)
    fields: dict[str, object] = dict(
        facility_id=fac.facility_id, name_ar=name_ar, name_latin=name_latin, sex=sex, dob=dob,
        dob_precision=precision, id_value=id_value, id_kind=id_kind, id_capture=id_capture,
        nationality=p.nationality if g.random() > 0.12 else None, phone=_phone(p, g, cfg),
        area=p.area if g.random() > 0.2 else None, registered_on=reg.isoformat(),
    )  # fmt: skip
    return Rendered(fields, style, tuple(log))


def g2_renderer(
    cfg: G2Config,
) -> Callable[[Person, People, Facility, date, np.random.Generator, str], Rendered]:
    def render(p: Person, people: People, fac: Facility, reg: date, g: np.random.Generator,
               file_no: str) -> Rendered:
        return render_record_g2(p, people, fac, reg, g, cfg, file_no)

    return render
