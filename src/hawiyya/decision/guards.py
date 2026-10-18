"""Hard guards on top of the model. Each guard can only lower a decision, never raise it.

| Guard | Fires when | Effect |
| --- | --- | --- |
| HARD_CONFLICT | two different card read identifiers of the same kind | at most REVIEW |
| POSSIBLE_TWIN_OR_SIBLING | dates of birth equal or close, family and father names agree, given names differ, and the identifiers do not agree | at most REVIEW |
| POSSIBLE_PARENT_CHILD_SHARED_ID | one identifier shared across a declared newborn substitute or a large age gap | at most REVIEW |
| PLACEHOLDER_ONLY | the shared identifier is a placeholder and the dates of birth do not agree exactly | at most REVIEW |
| COMMON_NAME_ONLY | all positive evidence comes from names, none from date, identifier or phone | at most REVIEW |
| DOB_PLACEHOLDER_SUSPECTED | the date of birth looks like a default value and the identifiers do not agree | at most REVIEW |
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from rapidfuzz.distance import Levenshtein

from hawiyya.contract.enums import ReasonCode
from hawiyya.contract.models import PairScore, Record
from hawiyya.normalise.identifiers import normalise_value
from hawiyya.normalise.names import ParsedName, parse_name

CLOSE_DOB = frozenset({"exact", "transposed", "digit1", "year_off"})
NAME_AGREE = frozenset({"exact", "skeleton", "coarse"})
GUARD_ORDER = (
    ReasonCode.HARD_CONFLICT,
    ReasonCode.POSSIBLE_TWIN_OR_SIBLING,
    ReasonCode.POSSIBLE_PARENT_CHILD_SHARED_ID,
    ReasonCode.PLACEHOLDER_ONLY,
    ReasonCode.COMMON_NAME_ONLY,
    ReasonCode.DOB_PLACEHOLDER_SUSPECTED,
)
NON_NAME_FIELDS = ("dob", "identifier", "phone")
NAME_FIELDS = ("given", "family", "father", "whole_name")


@dataclass(frozen=True)
class GuardInput:
    levels: Mapping[str, str]
    weights: Mapping[str, float]
    a: Record
    b: Record

    @staticmethod
    def from_score(score: PairScore, a: Record, b: Record) -> GuardInput:
        return GuardInput(
            {e.field: e.level for e in score.evidence},
            {e.field: e.weight for e in score.evidence},
            a,
            b,
        )


VOWEL_DISTANCE = 3  # ASSUMPTION: Latin spellings this many edits apart are different names


def _different_given(px: ParsedName, py: ParsedName) -> bool:
    """Different names, not spelling variants: different skeletons, or (Latin only) the same
    skeleton but spellings far apart, as with Hasan and Hussain."""
    if not px.given or not py.given:
        return False
    if px.given_key != py.given_key:
        return True
    if px.script == py.script == "latin":
        return int(Levenshtein.distance(px.given, py.given)) >= VOWEL_DISTANCE
    return False


def _given_tokens_differ(a: Record, b: Record) -> bool:
    """True when the given names differ in every rendering pair both records hold."""
    pairs = [(parse_name(x), parse_name(y)) for x in (a.name_ar, a.name_latin)
             for y in (b.name_ar, b.name_latin)]  # fmt: skip
    usable = [(px, py) for px, py in pairs if px and py]
    return bool(usable) and all(_different_given(px, py) for px, py in usable)


def hard_conflict(g: GuardInput) -> bool:
    return g.levels.get("identifier") == "different_reader"


def twin_or_sibling(g: GuardInput) -> bool:
    if g.levels.get("dob") not in CLOSE_DOB:
        return False
    if g.levels.get("family") not in NAME_AGREE:
        return False
    if g.levels.get("father") not in NAME_AGREE | {"missing"}:
        return False
    if g.levels.get("identifier") in ("exact", "edit1"):
        return False  # a strong identifier lets a LINK through
    return _given_tokens_differ(g.a, g.b)


def parent_child_shared_id(g: GuardInput) -> bool:
    return g.levels.get("identifier") == "shared_substitute"


def placeholder_only(g: GuardInput) -> bool:
    if g.levels.get("identifier") != "placeholder":
        return False
    same_value = normalise_value(g.a.id_value) == normalise_value(g.b.id_value)
    return same_value and g.levels.get("dob") != "exact"


def common_name_only(g: GuardInput) -> bool:
    name_pos = sum(max(0.0, g.weights.get(f, 0.0)) for f in NAME_FIELDS)
    other_pos = sum(max(0.0, g.weights.get(f, 0.0)) for f in NON_NAME_FIELDS)
    return name_pos > 0 and other_pos == 0.0


def dob_placeholder_suspected(g: GuardInput) -> bool:
    return g.levels.get("dob") == "placeholder" and g.levels.get("identifier") not in (
        "exact", "edit1")  # fmt: skip


CHECKS = {
    ReasonCode.HARD_CONFLICT: hard_conflict,
    ReasonCode.POSSIBLE_TWIN_OR_SIBLING: twin_or_sibling,
    ReasonCode.POSSIBLE_PARENT_CHILD_SHARED_ID: parent_child_shared_id,
    ReasonCode.PLACEHOLDER_ONLY: placeholder_only,
    ReasonCode.COMMON_NAME_ONLY: common_name_only,
    ReasonCode.DOB_PLACEHOLDER_SUSPECTED: dob_placeholder_suspected,
}


def fired(g: GuardInput) -> list[ReasonCode]:
    """Guards that fire for this pair, in a fixed order."""
    return [code for code in GUARD_ORDER if CHECKS[code](g)]
