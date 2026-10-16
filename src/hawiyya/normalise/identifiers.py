"""Identifier normalisation, structure validation, kind classification and pattern based
placeholder detection."""

from __future__ import annotations

import re
from dataclasses import dataclass

from hawiyya.contract.enums import IdCapture, IdKind

_STRIP = re.compile(r"[\s\-./]")
_EID = re.compile(r"^784\d{12}$")
_PASSPORT = re.compile(r"^[A-Z]{1,2}\d{6,9}$")
_GCC = re.compile(r"^\d{9,12}$")
_FILE = re.compile(r"^F\d+\d*-?\d+$")


@dataclass(frozen=True)
class NormId:
    value: str | None
    kind: IdKind | None
    capture: IdCapture | None
    valid_structure: bool
    placeholder: bool


def normalise_value(v: str | None) -> str | None:
    if v is None:
        return None
    s = _STRIP.sub("", v).upper()
    return s or None


def is_pattern_placeholder(v: str) -> bool:
    """Repeated digit, ascending or descending run, or 784 followed by zeros."""
    if not v.isdigit() or len(v) < 6:
        return False
    if len(set(v)) == 1:
        return True
    asc = "01234567890123456789"
    desc = "98765432109876543210"
    if v in asc or v in desc:
        return True
    if v.startswith("784") and set(v[3:]) <= {"0"}:
        return True
    return v[3:] in asc and v.startswith("784")


def classify(v: str) -> IdKind:
    """Infer the identifier kind from its structure alone."""
    if is_pattern_placeholder(v):
        return IdKind.PLACEHOLDER
    if _EID.match(v):
        return IdKind.EID
    if _PASSPORT.match(v):
        return IdKind.PASSPORT
    if _FILE.match(v):
        return IdKind.FILE_NO
    if _GCC.match(v):
        return IdKind.GCC_ID
    return IdKind.FILE_NO


def valid_structure(v: str, kind: IdKind) -> bool:
    if kind in (IdKind.EID, IdKind.MOTHER_EID):
        return bool(_EID.match(v)) and 1900 <= int(v[3:7]) <= 2026
    if kind == IdKind.PASSPORT:
        return bool(_PASSPORT.match(v))
    if kind == IdKind.GCC_ID:
        return bool(_GCC.match(v))
    return kind == IdKind.FILE_NO


def normalise_identifier(value: str | None, kind: IdKind | None,
                         capture: IdCapture | None) -> NormId:
    v = normalise_value(value)
    if v is None:
        return NormId(None, None, None, False, False)
    placeholder = kind == IdKind.PLACEHOLDER or capture == IdCapture.PLACEHOLDER
    placeholder = placeholder or is_pattern_placeholder(v)
    k = IdKind.PLACEHOLDER if placeholder else (kind or classify(v))
    return NormId(v, k, capture, valid_structure(v, k), placeholder)
