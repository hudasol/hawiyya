# ADR 0008: Calibration and its split

Status: accepted

## Decision

- Log odds are mapped to probabilities with isotonic regression (pool adjacent violators,
  written in `hawiyya.scoring.calibration` so each step keeps its counts).
- The interval for a probability is the central 95 percent interval of a Beta(k + 1,
  n - k + 1) posterior for the isotonic step the score falls in (k matches among n pairs).
  This is a per bin posterior, not a bootstrap.
- Fitting uses development seeds 1 to 3; checking uses seeds 4 and 5. Households, names and
  identifiers are generated per seed, so no family appears in both, and siblings never
  straddle the split. Evaluation uses seeds 6 to 30 and the sealed seeds, never a fitting
  seed.

## Consequences

The calibrator is fitted on G1 data with Tier S. On G2 or other tiers the same log odds may
mean something else; E3 and E8 report calibration error per generator. A step with few pairs
gets a wide interval, which the console shows.
