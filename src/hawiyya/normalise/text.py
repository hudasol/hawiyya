"""Script aware text normalisation, consonant skeleton, coarse key and Arabizi decoding.

Ported from Tahdeed ``src/tahdeed/normalize.py`` at commit
19657f7514037f43fcc6dc9e08c8bc855727678a (MIT, same author). Changes for person names:
street vocabulary and the place name stopwords are removed, script detection recognises
Arabizi, the article list is limited to forms seen in names, and a zero width and bidi
control stripper is added. Arabic letters are written as escapes so the source stays
readable on every console.

The skeleton is deliberately lossy: distinct common names collide (for example Hasan and
Hussain), so skeleton agreement is moderate evidence and never proof.
"""

from __future__ import annotations

import re
import unicodedata

_DIGIT_MAP = {ord(c): str(i) for i, c in enumerate("٠١٢٣٤٥٦٧٨٩")}
_DIGIT_MAP.update({ord(c): str(i) for i, c in enumerate("۰۱۲۳۴۵۶۷۸۹")})

_AR_DIACRITICS = re.compile("[ً-ٰٟۖ-ۭـ]")  # includes tatweel
_AR_RANGE = re.compile("[؀-ۿݐ-ݿࢠ-ࣿ]")
_LATIN_RANGE = re.compile("[A-Za-z]")
_INVISIBLE = re.compile("[​-‏‪-‮⁦-⁩﻿]")

_AR_UNIFY = str.maketrans({
    "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
    "ى": "ي", "ئ": "ي", "ؤ": "و", "ی": "ي",
    "ک": "ك", "ڤ": "ف", "پ": "ب", "چ": "ج",
    "گ": "ك", "ژ": "ز", "ۀ": "ه", "ہ": "ه",
    "ھ": "ه",
})  # fmt: skip


def to_ascii_digits(s: str) -> str:
    """Convert Arabic Indic and Persian digits to ASCII digits."""
    return s.translate(_DIGIT_MAP)


def has_arabic(s: str) -> bool:
    return bool(_AR_RANGE.search(s))


def has_latin(s: str) -> bool:
    return bool(_LATIN_RANGE.search(s))


def is_arabizi_token(w: str) -> bool:
    """A Latin token that mixes at least one digit and at least two letters."""
    return any(c.isdigit() for c in w) and sum(c.isalpha() for c in w) >= 2


def script_of(s: str) -> str:
    """Return 'ar', 'en', 'arabizi', 'mixed' or 'none'."""
    a, e = has_arabic(s), has_latin(s)
    if a and e:
        return "mixed"
    if a:
        return "ar"
    if e:
        toks = re.findall(r"[A-Za-z0-9]+", s)
        return "arabizi" if any(is_arabizi_token(t) for t in toks) else "en"
    return "none"


def normalize_arabic(s: str) -> str:
    """Strip diacritics and tatweel and unify letter variants. Ta marbuta is kept."""
    s = unicodedata.normalize("NFKC", s)
    s = _AR_DIACRITICS.sub("", s)
    return s.translate(_AR_UNIFY)


_APOS = re.compile("[’‘`´ʻʼʿʾ']")


def normalize_latin(s: str) -> str:
    """Lower case, strip accents and apostrophes, turn hyphens and underscores into spaces."""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = _APOS.sub("", s)
    s = s.replace("-", " ").replace("_", " ")
    return s.lower()


_TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)


def normalize_text(s: str) -> str:
    """Script aware canonical form: invisible marks removed, digits ASCII, Arabic unified,
    Latin lower case, whitespace collapsed."""
    s = _INVISIBLE.sub("", s)
    s = to_ascii_digits(s)
    s = normalize_arabic(s)
    s = normalize_latin(s)
    return " ".join(_TOKEN_RE.findall(s))


def tokenize(s: str) -> list[str]:
    return normalize_text(s).split()


# ----------------------------------------------------------------------------- skeleton

_AR_SKEL = {
    "ب": "b", "ت": "t", "ط": "t", "ث": "s", "س": "s", "ص": "s",
    "ج": "j", "خ": "X", "د": "d", "ض": "d", "ذ": "z", "ز": "z",
    "ظ": "z", "ر": "r", "ش": "S", "غ": "G", "ف": "f", "ق": "k",
    "ك": "k", "ل": "l", "م": "m", "ن": "n",
}  # fmt: skip
_WAW, _YA, _HA, _HHA = "و", "ي", "ه", "ح"

_LATIN_DIGRAPHS = [("sch", "S"), ("sh", "S"), ("kh", "X"), ("gh", "G"), ("th", "s"),
                   ("dh", "z"), ("ch", "j"), ("ph", "f"), ("ck", "k"), ("ts", "s")]  # fmt: skip
_LATIN_SINGLE = {
    "b": "b", "p": "b", "t": "t", "s": "s", "z": "z", "j": "j", "d": "d", "r": "r",
    "f": "f", "v": "f", "q": "k", "k": "k", "g": "k", "l": "l", "m": "m", "n": "n",
    "h": "h", "x": "ks",
}  # fmt: skip
_CAPITAL_CLASSES = "SXG"


def _collapse(s: str) -> str:
    """Collapse repeated letters; digits are kept."""
    out: list[str] = []
    for ch in s:
        if ch.isdigit() or not out or out[-1] != ch:
            out.append(ch)
    return "".join(out)


def _skeleton_arabic_word(w: str) -> str:
    out: list[str] = []
    n = len(w)
    for i, ch in enumerate(w):
        if ch in _AR_SKEL:
            out.append(_AR_SKEL[ch])
        elif ch == _WAW:
            if i == 0:
                out.append("w")
        elif ch == _YA:
            if i == 0:
                out.append("y")
        elif ch in (_HA, _HHA):
            if i != n - 1:
                out.append("h")
        elif ch.isdigit():
            out.append(ch)
    return _collapse("".join(out))


_ARABIZI = str.maketrans({"3": "", "2": "", "7": "h", "5": "X", "9": "s", "6": "t", "8": "G"})


def decode_arabizi(w: str) -> str:
    """Chat alphabet digits inside a word are letters: 3 and 2 dropped, 7 h, 5 kh, 9 s,
    6 t, 8 gh. Only for tokens that mix a digit and at least two letters."""
    if is_arabizi_token(w):
        return w.translate(_ARABIZI)
    return w


def _skeleton_latin_word(w: str) -> str:
    w = decode_arabizi(w)
    w = re.sub(r"c(?=[eiy])", "s", w)
    w = w.replace("c", "k")
    for a, b in _LATIN_DIGRAPHS:
        w = w.replace(a, b)
    out: list[str] = []
    n = len(w)
    for i, ch in enumerate(w):
        if ch in _CAPITAL_CLASSES:
            out.append(ch)
        elif ch in _LATIN_SINGLE:
            if ch == "h" and i == n - 1:
                continue
            out.append(_LATIN_SINGLE[ch])
        elif ch in ("w", "y"):
            if i == 0:
                out.append(ch)
        elif ch.isdigit():
            out.append(ch)
    return _collapse("".join(out))


def skeleton_word(w: str) -> str:
    """Consonant skeleton of one normalised token (either script)."""
    if has_arabic(w):
        return _skeleton_arabic_word(w)
    return _skeleton_latin_word(w)


LATIN_ARTICLES = frozenset({"al", "el", "ul", "il", "as", "ash", "ad", "adh", "az", "an", "ar", "at"})
_AL = "ال"


def strip_articles(tokens: list[str]) -> list[str]:
    """Drop definite articles (Latin tokens, and Arabic al glued to a word of 4+ letters)."""
    out: list[str] = []
    last = len(tokens) - 1
    for i, t in enumerate(tokens):
        if t in LATIN_ARTICLES and i != last:
            continue
        if t == _AL and i != last:
            continue
        if has_arabic(t) and t.startswith(_AL) and len(t) >= 4:
            t = t[2:]
        out.append(t)
    return out


def string_skeleton(s: str) -> str:
    """Joined skeleton of a whole string after normalisation and article removal."""
    return "".join(skeleton_word(t) for t in strip_articles(tokenize(s)))


_COARSE = str.maketrans({"X": "k", "G": "k", "j": "k", "y": "k", "q": "k", "g": "k",
                         "S": "s", "z": "s", "d": "t", "p": "b", "v": "f"})  # fmt: skip


def coarse_key(k: str) -> str:
    """Merge consonant classes that transliterations confuse (j g k kh gh, s z sh, d t)."""
    return _collapse(k.translate(_COARSE))
