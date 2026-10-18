# ADR 0013: The independent generator G2 and how its independence is enforced

Status: accepted

## Context

G1 and the matcher share ideas on purpose: G1 romanises Arabic with the transliteration ported
from Tahdeed, and the matcher normalises with the normalisation ported from Tahdeed. Tahdeed's
own evaluation showed that numbers measured on such a generator are optimistic.

## Decision

- G2 (`hawiyya.registry.g2`) renders names from the Arabic forms with its own tables and
  conventions (academic with hyphenated and assimilated articles, Maghrebi French spellings,
  a Levantine chat Arabizi with 2 for qaf and capital letters for emphatics), and adds
  heavier noise: keyboard adjacent typos in both scripts, OCR confusions, truncated family
  names, honorifics, swapped order, married women under the husband's family name, mixed
  script entries, doubled spaces, zero width characters, two digit identifier typos, a mid
  month default date and formatted phone numbers.
- An import contract (`pyproject.toml`, "Independence") forbids G2 from importing
  `hawiyya.normalise`, `hawiyya.registry.g1`, `hawiyya.matching` and `hawiyya.scoring`. A
  test runs the contract.
- G2 shares the people (households, twins, identifiers, facilities) with G1, so a G1 versus
  G2 comparison isolates the rendering of the registration.
- Every system is evaluated on both (E8) and the drop is reported per system.

## Consequences

G2 is one alternative world written by the same author; it is not an independent test in the
scientific sense, and the documents say so. The frozen model is fitted on G1 only, so E8 also
measures how far calibration transfers.
