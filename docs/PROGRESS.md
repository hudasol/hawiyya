# Progress

Updated at every phase gate. A fresh session can continue from this file, the git log and
`hawiyya check`.

## Preflight (2026-10-13)

| Check | Result |
| --- | --- |
| Python | 3.13.0 via `py -3.13` (`python` alias not on PATH); virtual environment in `.venv` |
| Node and npm | Node 24.15.0, npm 11.12.1 |
| git identity | user.name and user.email are set (not changed) |
| Free disk | about 119 GB |
| pip registry | reachable (packages installed) |
| Java | OpenJDK 21.0.10 present, so Synthea runs; no install needed |
| Tahdeed reference clone | `.sikka/refs/tahdeed` at commit 19657f7514037f43fcc6dc9e08c8bc855727678a |
| Playwright Chromium | checked in P4 when the web app is created |

## Phases

| Phase | State | Evidence | Tag |
| --- | --- | --- | --- |
| P0 skeleton, tooling, contracts, harness | done | `hawiyya check` passes (ruff, mypy strict, three import contracts, tests) | v0.1.0 |
| P1 contract and registry | done | contract tests; same seed gives byte identical registry; Tier S 5,000 persons (about 11,800 records), Tier M 20,000 persons (slow test); `results/lexicon_report.json` | v0.2.0 |
| P2 normalisation | next | | v0.3.0 |
| P3 matching | not started | | v0.4.0 |
| P4 scoring and walking skeleton | not started | | v0.5.0 |
| P5 decision | not started | | v0.6.0 |
| P6 workflow | not started | | v0.7.0 |
| P7 lab | not started | | v0.8.0 |
| P8 evaluation | not started | | v0.9.0 |
| P9 console | not started | | v0.10.0 |
| P10 hardening | not started | | v1.0.0 |

## State of the data

- Data source: Synthea (25,000 living patients, ten deterministic chunks, reference date
  2026-01-01). Raw output in `.sikka/synthea/` (private); derived sample committed in
  `data/samples/population.csv.gz`; provenance in `data/MANIFEST.json`.
- Lexicon: `data/lexicon/names.json`, author `build_agent`. No Cowork inputs have arrived
  (`inputs/cowork/` absent at the P1 boundary).
- Public sources A to D opened and checked; see `docs/CONTEXT.md`.

## Next

P2: person name model, date and identifier normalisation, pattern and learned placeholder
detection, term frequency tables, golden table and property tests.

## Blockers

None.
