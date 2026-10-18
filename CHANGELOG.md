# Changelog

All notable changes are listed per phase tag.

## v0.6.0 (P5)

- L5 decision: cost based thresholds, guards with reason codes, fail closed rule, batch
  decisions, conflict aware clustering, bilingual explanations, next best question.
- The check endpoint and the console show decisions.

## v0.5.0 (P4)

- L4 scoring: parameters with sign constraints, plain EM, anchored estimation, label fit,
  term frequency adjustment, isotonic calibration with Beta intervals, frozen model.
- Walking skeleton: registration check (fails open), FastAPI service, static snapshot, and
  the console with three screens in English and Arabic.

## v0.4.0 (P3)

- L3 matching: multi pass blocking with a cap and sorted neighbourhood fallback, symmetric
  comparison levels for ten fields, blocking smoke check.

## v0.3.0 (P2)

- L2 normalisation: ported text normalisation, person name model, dates, identifiers,
  pattern and learned placeholder detection, term frequencies, vowel aware similarity.
- Generator: most placeholders are now typed as ordinary identifiers.

## v0.2.0 (P1)

- L0 contract models, enums, bilingual reason codes and generated artefacts.
- L1 registry: Synthea adapter and native fallback, data manifest, lexicon and denylist,
  identity layer, six facilities, G1 corruption engine, truth view, lexicon report.

## v0.1.0 (P0)

- Repository layout, tooling, fast check (`hawiyya check`), import contracts for layers,
  independence and label isolation, traceability and claims harness, ADR 0001.
