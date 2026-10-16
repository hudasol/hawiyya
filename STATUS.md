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
- Scoring, decisions, the API and the console do not exist yet.
