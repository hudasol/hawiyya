"""G1 romanisation of Arabic names in three styles: formal, gulf and arabizi.

Ported from Tahdeed ``src/tahdeed/noise2.py`` at commit
19657f7514037f43fcc6dc9e08c8bc855727678a (MIT, same author), with these changes: it works on
person names instead of place names, takes a numpy generator, and drops the address specific
parts. G1 shares ideas with the matcher on purpose; G2 does not import this module.
"""

from __future__ import annotations

import numpy as np

STYLES = ("formal", "gulf", "arabizi")

_MAP: dict[str, dict[str, list[str]]] = {
    "ب": {"*": ["b"]},
    "ت": {"*": ["t"]},
    "ث": {"formal": ["th"], "gulf": ["th", "s", "t"], "arabizi": ["th", "s"]},
    "ج": {"formal": ["j"], "gulf": ["j", "y", "j"], "arabizi": ["j", "g"]},
    "ح": {"formal": ["h"], "gulf": ["h"], "arabizi": ["7", "h"]},
    "خ": {"formal": ["kh"], "gulf": ["kh", "k"], "arabizi": ["5", "kh"]},
    "د": {"*": ["d"]},
    "ذ": {"formal": ["dh"], "gulf": ["z", "dh", "d"], "arabizi": ["th", "z", "d"]},
    "ر": {"*": ["r"]},
    "ز": {"*": ["z"]},
    "س": {"*": ["s"]},
    "ش": {"formal": ["sh"], "gulf": ["sh"], "arabizi": ["sh", "ch"]},
    "ص": {"formal": ["s"], "gulf": ["s"], "arabizi": ["9", "s"]},
    "ض": {"formal": ["d"], "gulf": ["d", "dh"], "arabizi": ["d"]},
    "ط": {"formal": ["t"], "gulf": ["t"], "arabizi": ["6", "t"]},
    "ظ": {"formal": ["z"], "gulf": ["z", "dh"], "arabizi": ["z", "th"]},
    "ع": {"formal": ["", "a"], "gulf": ["", "a"], "arabizi": ["3", "a"]},
    "غ": {"formal": ["gh"], "gulf": ["gh", "g"], "arabizi": ["8", "gh"]},
    "ف": {"*": ["f"]},
    "ق": {"formal": ["q"], "gulf": ["g", "q"], "arabizi": ["q", "9", "g"]},
    "ك": {"formal": ["k"], "gulf": ["k", "ch", "k"], "arabizi": ["k"]},
    "ل": {"*": ["l"]},
    "م": {"*": ["m"]},
    "ن": {"*": ["n"]},
    "ه": {"*": ["h", ""]},
    "ء": {"formal": [""], "gulf": [""], "arabizi": ["2", ""]},
    "أ": {"*": ["a", ""]},
    "إ": {"*": ["i", "e"]},
    "آ": {"*": ["aa", "a"]},
    "ؤ": {"*": ["o", "u"]},
    "ئ": {"*": ["e", "y", "i"]},
    "گ": {"*": ["g"]},
    "چ": {"*": ["ch"]},
    "پ": {"*": ["p", "b"]},
    "ڤ": {"*": ["v", "f"]},
}
_LONG = {
    "ا": ["a", "aa", "a"],
    "و": ["ou", "oo", "u", "o"],
    "ي": ["i", "ee", "y", "ie"],
    "ى": ["a", "y", "i"],
}
_SUN = set("تثدذرزسشصضطظلن")
_VOW = ["a", "a", "a", "e", "i", "u", "o"]
_TA_MARBUTA = "ة"
_AL = "ال"


def _pick(g: np.random.Generator, opts: list[str]) -> str:
    return opts[0] if g.random() < 0.55 else opts[int(g.integers(0, len(opts)))]


def translit_word(w: str, g: np.random.Generator, style: str) -> str:
    """Romanise one Arabic word in the given style. Short vowels are inserted at random."""
    out: list[str] = []
    prev_cons = False
    for i, ch in enumerate(w):
        if ch in _LONG:
            opts = _LONG[ch]
            if ch == "و" and i == 0:
                opts = ["w", "u"]
            if ch == "ي" and i == 0:
                opts = ["y", "i"]
            if ch == "ا" and i == 0:
                opts = ["a", "e"]
            out.append(_pick(g, opts))
            prev_cons = False
            continue
        if ch == _TA_MARBUTA:
            out.append(_pick(g, ["a", "ah", "a", "eh"]))
            prev_cons = False
            continue
        table = _MAP.get(ch)
        if table is None:
            out.append(ch if ch.isascii() and ch.isalnum() else "")
            continue
        opts = table.get(style) or table.get("*") or table.get("formal") or [""]
        s = _pick(g, opts)
        if prev_cons and s and g.random() < 0.75:
            out.append(_VOW[int(g.integers(0, len(_VOW)))])
        out.append(s)
        prev_cons = bool(s) and s[-1].isalpha()
    return "".join(out)


def translit_name(text: str, g: np.random.Generator, style: str) -> str:
    """Romanise a space separated Arabic name. Handles the article and compound names."""
    words: list[str] = []
    for w in text.split():
        if w.startswith(_AL) and len(w) > 3:
            base = w[2:]
            art = "al" if g.random() < 0.8 else "el"
            if style == "formal" and base[0] in _SUN and g.random() < 0.3:
                first = translit_word(base[0], g, style)
                art = "a" + (first or "l")
            glue = g.random() < 0.25
            body = translit_word(base, g, style)
            words.append(art + body if glue else art + " " + body)
        elif w.startswith("عبد") and len(w) > 4:
            rest = w[3:]
            head = _pick(g, ["abdul", "abdel", "abd al", "abd ul", "abdal"])
            if rest.startswith(_AL):
                rest = rest[2:]
            body = translit_word(rest, g, style)
            words.append(head + body if g.random() < 0.5 else head + " " + body)
        else:
            words.append(translit_word(w, g, style))
    s = " ".join(x for x in words if x)
    return s.title() if style != "arabizi" and g.random() < 0.7 else s
