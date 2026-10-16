"""Vowel aware whole name similarity (an optional extra comparison level).

The skeleton drops vowels, so Hasan and Husain look alike. This second pass compares whole
normalised Latin strings with Jaro Winkler similarity, which does see vowels. It is used
only as an extra level, never on its own.
"""

from __future__ import annotations

from rapidfuzz.distance import JaroWinkler

from hawiyya.normalise.names import ParsedName


def whole_name_similarity(a: ParsedName, b: ParsedName) -> float | None:
    """Similarity in [0, 1] of two Latin names, or None when either is not Latin."""
    if a.script != "latin" or b.script != "latin":
        return None
    sa, sb = " ".join(a.tokens), " ".join(b.tokens)
    return float(JaroWinkler.normalized_similarity(sa, sb))
