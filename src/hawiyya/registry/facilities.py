"""Synthetic facilities and their registration styles.

Six synthetic facilities, each with a registration style. Facility names are neutral codes;
no real facility is modelled. Every rate is an ASSUMPTION chosen by the author.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Facility:
    facility_id: str
    style: str
    description: str
    reader_share: float  # share of resident identifiers captured by card reader
    placeholder_rate: float  # share of records given a placeholder identifier
    id_typo_rate: float  # share of manually typed identifiers with one error
    dob_default_rate: float  # share of dates of birth replaced by a default first of January
    scripts: tuple[str, ...]  # which name fields are captured: "ar", "latin"
    latin_style: str  # "card", "variant", "gulf", "arabizi"
    noise: float  # multiplier on name corruption rates
    weight: float  # relative share of registrations


FACILITIES: tuple[Facility, ...] = (
    Facility("F1", "card_reader", "Identifier captured by card reader; both scripts from the card",
             reader_share=0.95, placeholder_rate=0.005, id_typo_rate=0.0, dob_default_rate=0.0,
             scripts=("ar", "latin"), latin_style="card", noise=0.3, weight=1.3),
    Facility("F2", "manual_entry", "Identifier typed by hand; Latin names with spelling variants",
             reader_share=0.0, placeholder_rate=0.03, id_typo_rate=0.10, dob_default_rate=0.01,
             scripts=("latin",), latin_style="variant", noise=1.0, weight=1.0),
    Facility("F3", "high_placeholder", "Busy walk in desk with a high placeholder rate",
             reader_share=0.2, placeholder_rate=0.35, id_typo_rate=0.06, dob_default_rate=0.12,
             scripts=("latin",), latin_style="variant", noise=1.3, weight=0.9),
    Facility("F4", "arabic_only", "Names entered in Arabic script only",
             reader_share=0.3, placeholder_rate=0.04, id_typo_rate=0.06, dob_default_rate=0.01,
             scripts=("ar",), latin_style="card", noise=1.0, weight=0.9),
    Facility("F5", "english_only", "Names entered in Latin script only, Gulf style transliteration",
             reader_share=0.5, placeholder_rate=0.03, id_typo_rate=0.05, dob_default_rate=0.01,
             scripts=("latin",), latin_style="gulf", noise=1.0, weight=1.0),
    Facility("F6", "mobile_app", "Self registration in a mobile app; Arabizi and casual typing",
             reader_share=0.0, placeholder_rate=0.05, id_typo_rate=0.08, dob_default_rate=0.02,
             scripts=("latin",), latin_style="arabizi", noise=1.4, weight=0.8),
)  # fmt: skip

BY_ID = {f.facility_id: f for f in FACILITIES}

# ASSUMPTION: placeholder values. "All 1" (fifteen ones) follows the public policy reading in
# docs/CONTEXT.md; the other values are plausible defaults chosen by the author. The last one
# imitates a clerk's habitual dummy number that looks valid, which only a data driven
# detector can find.
PLACEHOLDER_VALUES: tuple[tuple[str, float], ...] = (
    ("111111111111111", 0.62),
    ("000000000000000", 0.08),
    ("999999999999999", 0.06),
    ("784000000000000", 0.06),
    ("123456789012345", 0.04),
    ("784199054321987", 0.14),
)
SANCTIONED_PLACEHOLDER = "111111111111111"
# ASSUMPTION: share of "All 1" entries flagged as placeholders on the form; the rest, and all
# other placeholder values, are typed into the identifier field as if they were real.
SANCTIONED_FLAGGED_SHARE = 0.6
