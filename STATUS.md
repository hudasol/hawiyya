# Status

What works today, in plain words.

- `hawiyya check` runs lint, strict type checks, import contracts (layers, G2
  independence, label isolation), the fast tests and the traceability check.
- The L0 contract defines every model; JSON Schema, TypeScript types and a bilingual field
  dictionary are generated from it and checked for staleness.
- `build_registry(seed, tier)` produces a deterministic synthetic registry from a Synthea
  population: households, twins, cousins, same name fathers and sons, newborns under the
  mother's identifier, placeholders, six synthetic facilities and the G1 corruption engine.
  Ground truth lives in a separate truth view.
- L2 normalises Arabic, English and Arabizi names into tokens with given, father,
  grandfather and family positions, consonant skeletons and coarse keys; parses dates and
  identifiers; flags placeholders by pattern and by a data driven rule; and builds term
  frequency tables from the registry itself.
- L3 finds candidate pairs with seven blocking passes (placeholders never block) and gives
  each pair a discrete agreement level per field.
- L4 scores pairs with a Fellegi Sunter model (anchored estimation, frequency adjustment,
  isotonic calibration with intervals); every score carries an evidence table that adds up.
- The API serves health, registry summary, registration check, pair score and name analysis;
  the console shows Overview, Registration check and Name lab in English and Arabic, in live
  or static mode.
- L5 turns each score into LINK (recommend a merge request), REVIEW or KEEP_APART by
  explicit costs, with six guards that can only lower a LINK, conflict aware clustering,
  three sentence explanations in English and Arabic, and a next best question.
- The review queue, audit log, exports and the experiments do not exist yet.
