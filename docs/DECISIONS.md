# Decisions log

Decisions taken where the build brief was silent or ambiguous, with the reason. Larger
decisions have their own ADR in `docs/adr/`.

| # | Decision | Reason |
| --- | --- | --- |
| D-001 | Requirements and claims sources live in `spec/requirements.json` and `spec/claims.json`; `docs/TRACEABILITY.md` and `docs/CLAIMS.md` are rendered from them. | Keeps one machine readable source of truth and lets a test check freshness. |
| D-002 | Traceability is enforced progressively: a MUST requirement is checked once the phase that delivers it is complete (`spec/phase.json`). | The fast check must pass on every commit, including the empty skeleton, without weakening the rule at the end (by P10 every phase is enforced). |
| D-003 | Tests name requirements through `pytest.mark.req("HW-...")`; web tests name them in a comment or test title. | A simple text scan finds both and works across Python and TypeScript. |
| D-004 | The CLI lives in `hawiyya.cli`, placed above `hawiyya.api` in the layer contract. | It orchestrates every layer, so it must be the top layer. |
| D-005 | Cross cutting code (`hawiyya.core`) is the lowest layer and imports nothing from Hawiyya. | Any layer may use configuration, determinism and logging helpers without creating a cycle. |
| D-006 | The logging helper module is named `safelog` rather than `logging`. | Avoids shadowing the standard library module name. |
| D-007 | Household, clan, twin and identifier structure lives in a neutral module (`hawiyya.registry.people`) that renders no text; G1 and G2 each render names with their own rules. | Both generators need the same people for a fair G1 versus G2 comparison, while the independence contract only concerns name rendering and noise. |
| D-008 | Twins are made by aligning one sibling's Synthea birth date to the other's. | Synthea does not emit twins; the brief requires them as hard negatives. |
| D-009 | Registration dates fall between 2023-01-01 and 2026-09-30; a newborn's first registration falls within 60 days of birth. | Gives newborns a window in which the mother's identifier substitute applies (under 90 days). |
| D-010 | A tier `XS` (600 persons) exists for fast tests only. | Keeps the fast check fast; no result is reported on XS. |
| D-011 | The lexicon report measures collisions over canonical spellings with whole string skeletons. | It must be produced in P1, before the person name model (P2); P2 adds name model keys. |
| D-012 | Project tools are run through the `py` launcher from a helper outside the repository. | `.venv` executables are not on the pre approved command list; `py` is. |
