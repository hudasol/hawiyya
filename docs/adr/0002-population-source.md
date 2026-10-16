# ADR 0002: Population source (Synthea, with a native fallback)

Status: accepted

## Context

The registry needs synthetic people with realistic structure (ages, sexes, encounter
counts). Synthea is free (Apache License 2.0) and needs Java 17 or newer. The build machine
had OpenJDK 21, so Synthea could run.

## Decision

- Synthea is the population source. The latest release jar (tag `master-branch-latest`) is
  downloaded with Python `urllib`, hashed, and kept in `.sikka/tools/` (never committed).
- 25,000 living patients are generated in ten deterministic runs of 2,500 (seeds 20261013
  to 20261022) with the reference date fixed at 2026-01-01, so birth dates do not depend on
  the day of the build. Runs are chunked so an interrupted build resumes without changing
  the result. Only `patients.csv` and `encounters.csv` are exported.
- A derived sample (`data/samples/population.csv.gz`, about 0.7 MB) with five columns is
  committed with `data/NOTICE.md`. A clean clone builds every registry from it without Java.
- A native generator with the same schema exists as a fallback and for tests. The data
  source is a field in `data/MANIFEST.json`; the README and data statement render their
  source line from it, and a test fails when they disagree.
- Each tier samples persons from the pool with the tier seed. The same Synthea person can
  appear in several seeds, but households, names and identifiers are drawn anew per seed,
  so no family is shared between seeds.

## Consequences

Synthea's demographics are those of a simulated United States population, not the UAE's.
This is stated in the data statement. Tier L (100,000 persons) cannot be drawn from a pool
of 25,000 without repetition; it is a MAY item and is recorded in `docs/KNOWN_ISSUES.md`.
