# ADR 0005: Comparison levels and blocking

Status: accepted

## Context

A Fellegi Sunter model needs discrete agreement levels per field, and the registry is too
large to compare every pair.

## Decision: comparison levels

Defined in `hawiyya.matching.levels` and computed in `hawiyya.matching.compare`.

| Field | Levels (strongest first) | Notes |
| --- | --- | --- |
| given, family, father | exact, skeleton, coarse, edit1, initial, missing, mismatch | Exact needs the same script; skeleton and coarse work across scripts; the best alignment over every name rendering both records hold is used; a swapped given and family order is accepted only when both swapped tokens agree. |
| whole name | very close, close, far, not comparable | Jaro Winkler on Latin strings only (sees vowels); an extra level. |
| date of birth | exact, transposed, digit1, year off, year only, missing, placeholder, conflict | A date flagged as a placeholder (pattern or learned) gives the placeholder level. |
| sex | agree, missing, disagree | |
| identifier | exact, edit1, shared substitute, missing, placeholder, different kinds, different manual, different reader | Placeholders give the placeholder level; the same value across a declared newborn substitute or an age gap of 12 years or more is a shared substitute; a disagreement between two card read identifiers is its own, stronger level. |
| phone, nationality, area | agree, missing, different | weak fields |

The missing and placeholder levels are neutral: L4 gives them a weight of exactly zero.
Every comparison is symmetric in record order (tested with hypothesis).

## Decision: blocking

Seven passes (family skeleton and birth year; given skeleton and date of birth; identifier
tail; identifier head; phone; sorted given and family coarse keys; date of birth and family
coarse key), united. Placeholder identifiers never produce a key. Blocks larger than 60
records are not expanded in full; their records are sorted by given key and date of birth
and each is paired with its next 12 neighbours (sorted neighbourhood fallback). The cap and
window are ASSUMPTION values; the completeness lost to the cap is reported.

## Consequences

Conditional independence between fields is violated (given, father and whole name levels
are correlated, and siblings share father, family, phone and area). Calibration in L4 is the
repair, and its quality is measured. Swapped order alignment can hide which token was the
given name; the evidence table reports the aligned levels.
