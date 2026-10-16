"""Person name model: tokens and structure for Arabic, English and Arabizi names.

Steps: normalise text, strip honorifics, expand common abbreviations, join compound given
names (Abd Al Rahman, Abdul Rahman, Saif Ullah), drop connectors (bin, ibn, bint) while
noting that the next token is the father's name, strip definite articles (separate or
glued), then assign given, father, grandfather and family positions.

The tables here belong to the matcher and are written independently of the generator's
lexicon: the matcher never reads the lexicon.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from hawiyya.normalise.text import coarse_key, has_arabic, skeleton_word, tokenize

HONORIFICS_LATIN = frozenset({"mr", "mrs", "ms", "miss", "dr", "sheikh", "shaikh", "sh", "eng",
                              "prof", "sayed", "sayyid", "hajj", "haji"})  # fmt: skip
HONORIFICS_AR = frozenset({"السيد", "السيدة",
                           "الشيخ", "دكتور",
                           "د"})  # fmt: skip
CONNECTORS = frozenset({"bin", "ibn", "bint", "binte", "binti",
                        "بن", "ابن", "بنت"})  # fmt: skip
ABBREVIATIONS = {"mohd": "mohammed", "md": "mohammed", "muhd": "mohammed", "mhd": "mohammed"}
# Names that begin with al or el but carry no article.
AL_NAMES = frozenset({"alexander", "alexandra", "alexis", "alan", "albert", "alfred", "alice",
                      "alicia", "alison", "allison", "ellen", "elena", "elias", "elizabeth",
                      "ella", "ellie", "elham", "alaa", "alia", "aliya", "alina", "elliot"})  # fmt: skip
ABD_HEADS = frozenset({"abd", "abdul", "abdel", "abdal", "abdol", "abdu"})
ABD_AR = "عبد"
SUFFIX_PARTS = frozenset({"ullah", "allah", "uddin", "eddin", "addin", "aldin"})
KUNYA = frozenset({"abu", "umm", "um", "bu", "ابو", "ام"})
ARTICLES = frozenset({"al", "el", "ul"})
AL_AR = "ال"


@dataclass(frozen=True)
class ParsedName:
    raw_tokens: tuple[str, ...]
    tokens: tuple[str, ...]
    given: str | None
    father: str | None
    grandfather: str | None
    family: str | None
    initials: frozenset[str]
    had_connector: bool
    script: str  # "ar" or "latin"

    @property
    def given_key(self) -> str:
        return skeleton_word(self.given) if self.given else ""

    @property
    def family_key(self) -> str:
        return skeleton_word(self.family) if self.family else ""

    def keys(self) -> tuple[str, ...]:
        return tuple(skeleton_word(t) for t in self.tokens)


def _strip_article(t: str, family_position: bool) -> str:
    if has_arabic(t):
        if t.startswith(AL_AR) and len(t) >= 4:
            return t[2:]
        return t
    # Glued Latin article (Almazrouei): only in family position and on longer tokens, because
    # given names such as Ali or Alia begin with the same letters.
    if family_position and len(t) >= 6 and t[:2] in ("al", "el") and t not in AL_NAMES:
        return t[2:]
    return t


@lru_cache(maxsize=200_000)
def parse_name(text: str | None) -> ParsedName | None:
    """Parse a name string into a token structure. Returns None for an empty name."""
    if not text:
        return None
    raw = tokenize(text)
    if not raw:
        return None
    script = "ar" if any(has_arabic(t) for t in raw) else "latin"
    toks = list(raw)
    while len(toks) > 2 and (toks[0] in HONORIFICS_LATIN or toks[0] in HONORIFICS_AR):
        toks = toks[1:]
    toks = [ABBREVIATIONS.get(t, t) for t in toks]
    joined: list[str] = []
    i = 0
    father_hint: int | None = None
    had_connector = False
    while i < len(toks):
        t = toks[i]
        nxt = toks[i + 1] if i + 1 < len(toks) else None
        if t in CONNECTORS and nxt is not None and joined:
            had_connector = True
            if father_hint is None:
                father_hint = len(joined)
            i += 1
            continue
        if (t in ABD_HEADS or t == ABD_AR) and nxt is not None:
            if nxt in ARTICLES and i + 2 < len(toks):
                joined.append(t + nxt + toks[i + 2])
                i += 3
                continue
            joined.append(t + nxt)
            i += 2
            continue
        if t in KUNYA and nxt is not None and nxt not in ARTICLES:
            joined.append(t + nxt)
            i += 2
            continue
        if t in SUFFIX_PARTS and joined:
            joined[-1] = joined[-1] + t
            i += 1
            continue
        if t in ARTICLES and nxt is not None:
            # A separate article belongs to the next word; drop it.
            i += 1
            continue
        if t == AL_AR and nxt is not None:
            i += 1
            continue
        joined.append(t)
        i += 1
    if not joined:
        return None
    last = len(joined) - 1
    joined = [_strip_article(t, i == last) for i, t in enumerate(joined)]
    initials = frozenset(t for t in joined if len(t) == 1 and not t.isdigit())
    given = joined[0]
    family = joined[-1] if len(joined) >= 2 else None
    father = grandfather = None
    if len(joined) >= 3:
        father = joined[father_hint] if father_hint and father_hint < last else joined[1]
        if len(joined) >= 4:
            grandfather = joined[2]
    return ParsedName(tuple(raw), tuple(joined), given, father, grandfather, family,
                      initials, had_connector, script)  # fmt: skip


def token_keys(token: str) -> tuple[str, str]:
    """Skeleton and coarse key of one normalised token."""
    k = skeleton_word(token)
    return k, coarse_key(k)
