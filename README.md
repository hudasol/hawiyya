# Hawiyya

Work in progress. See `STATUS.md` for what works today.

All patients in this repository are synthetic. Identifiers are synthetic and belong to no
person.

## Data

<!-- BEGIN:data_source -->
Data source: Synthea

- Synthea release tag `master-branch-latest`, jar SHA 256 `018ad7f04f7aacb995804d7d4781c76d5fc714f7f23257ba50daa9eefae224ac`.
- 10 deterministic runs, reference date 2026-01-01, 25000 living synthetic patients kept.
- Kept columns: `person_id`, `birth_date`, `sex`, `region`, `encounters`.
- Name lexicon author: `build_agent`.
- Exact commands and file hashes: `data/MANIFEST.json`.
<!-- END:data_source -->
