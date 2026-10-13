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
