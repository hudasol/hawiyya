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
| Java | OpenJDK 21.0.10 present, so Synthea can run; no install needed |
| Tahdeed reference clone | `.sikka/refs/tahdeed` at commit 19657f7514037f43fcc6dc9e08c8bc855727678a |
| Playwright Chromium | checked in P4 when the web app is created |

## Phases

| Phase | State | Tag |
| --- | --- | --- |
| P0 skeleton, tooling, contracts, harness | done (`hawiyya check` passes: ruff, mypy strict, three import contracts, 7 tests) | v0.1.0 |
| P1 contract and registry | in progress | v0.2.0 |
| P2 normalisation | not started | v0.3.0 |
| P3 matching | not started | v0.4.0 |
| P4 scoring and walking skeleton | not started | v0.5.0 |
| P5 decision | not started | v0.6.0 |
| P6 workflow | not started | v0.7.0 |
| P7 lab | not started | v0.8.0 |
| P8 evaluation | not started | v0.9.0 |
| P9 console | not started | v0.10.0 |
| P10 hardening | not started | v1.0.0 |

## Next

P1: L0 contract models and generators, then L1 registry. A Synthea population of 25,000
is being generated in ten deterministic chunks of 2,500 (seeds 20261013 to 20261022,
reference date 2026-01-01) under `.sikka/synthea/`; the run resumes chunk by chunk.

## Blockers

None.
