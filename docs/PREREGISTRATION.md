# Preregistration

Written and committed before any experiment in this file was run. Numeric predictions are in
`docs/PREDICTIONS.md` and, in machine readable form, in `spec/predictions.json`; the
evaluation document marks each one HIT or MISS automatically from `results/`.

## What had been seen before writing this

Honesty about prior exposure: before these predictions were written the author had seen
(a) model fitting diagnostics on development seeds 1 to 5 (`results/model/fit_report.json`:
calibration error and average precision of plain EM, anchored estimation and the label fit),
(b) a blocking smoke check on development seed 7 (`results/dev/blocking_smoke.json`), and
(c) a handful of registration checks on the demonstration registry (development seed 7). No
baseline, no G2 registry, no sealed seed and no per stratum result had been computed.

## The world is synthetic and shares an author with the method

The synthetic registry, the identity layer, the G1 corruption engine, the lexicon and the
matcher were all written by the same build agent. G1 and the matcher share ideas on purpose
(ported Tahdeed transliteration on the generator side, ported Tahdeed normalisation on the
matcher side). G2 is a second generator written with separate tables and heavier noise and is
forbidden by an import contract from using the matcher's or G1's code. G2 is still written by
the same author, so it is one alternative world, not an independent test.

## Seeds and splits

| Use | Seeds | Generator | Tier |
| --- | --- | --- | --- |
| Model fitting (EM, anchors, label fit, isotonic calibration, GBM reference, B3 refit) | 1, 2, 3 | G1 | S |
| Calibration check (already seen) | 4, 5 | G1 | S |
| Development evaluation, G1 | 6 to 25 (20 seeds) | G1 | S |
| Development evaluation, G2 | 6 to 15 (10 seeds) | G2 | S |
| Placeholder sweep (E5) | 6 to 10 (5 seeds) per level | G1 | S |
| Headline run | 26 to 30 (5 seeds) | G1 | M |
| Sealed evaluation, G1 | 1001 to 1020 (20 seeds) | G1 | S |
| Sealed evaluation, G2 | 1021 to 1030 (10 seeds) | G2 | S |
| Sealed placeholder sweep | 1001 to 1005 | G1 | S |

The brief suggested 30 seeds per study; the counts above are reduced so that the whole suite
fits in about 30 minutes on a laptop, and the reduction is stated here in advance. Sealed seeds
are generated only by `hawiyya eval --sealed`, which runs once after all tuning is frozen, and
writes `results/SEALED_RUN.json` with the commit hash and a timestamp. Households, names and
identifiers are generated per seed, so no family appears in both fitting and evaluation.

## Systems (all decide on the same pair universe)

The pair universe of a registry is the union of Hawiyya's blocking candidates, every pair whose
normalised identifier strings are equal, and every pair with an equal normalised name and date
of birth. A system that does not consider a pair keeps it apart. True pairs outside the universe
count as missed for every system.

| Key | System |
| --- | --- |
| B0_eid_exact | LINK when the normalised identifier strings are equal (any value, placeholders included), as a status quo rule would. |
| B1_name_dob_exact | LINK when some rendering of the two names is equal after normalisation and the dates of birth are equal. |
| B2_fuzzy_raw | LINK when the token set similarity of the raw name strings (rapidfuzz) is at least 90 and the dates of birth are equal. |
| B3_latin_only | Hawiyya without Arabic and skeleton handling: Arabic names dropped and skeleton, coarse and edit levels treated as mismatch; parameters and calibration refitted on seeds 1 to 3. |
| B4_forced | Hawiyya's probability with no review: LINK when p >= 0.5, otherwise keep apart; no guards. |
| B5_hawiyya | The product: costs C_FM 500, C_MD 20, C_R 2, guards, clustering. |
| B6_gbm | Reference: gradient boosted trees on the same levels and frequencies, trained with labels on seeds 1 to 3, isotonic calibrated, the same costs, no guards. |

## Metrics (never collapsed to one number)

Per system and seed: precision, recall and F1 of automatic LINKs over pairs; false merges per
10,000 records (false LINK pairs per 10,000 records); found recall (share of true pairs that
are LINK or REVIEW); review rate (REVIEW pairs per 1,000 records); B cubed precision and recall
of clusters (connected components of LINK edges for baselines, conflict checked clusters for
Hawiyya). Means across seeds with 95 percent t intervals; proportions pooled across seeds also
get Wilson intervals. Weighted cost appears only in E9, with the weights shown.

## Experiments

| ID | Question | Main metric |
| --- | --- | --- |
| E1 | Does blocking keep the true pairs at a small cost? | pair completeness, reduction ratio, completeness lost to the cap; G1 and G2 |
| E2 | How do the product and the baselines compare? | all system metrics, G1 |
| E3 | Is the probability calibrated and does abstention work? | ECE, reliability, risk coverage, auto LINK precision, review share; estimation gap |
| E4 | Which name styles and corruptions are hardest? | found recall by name style and by corruption tag |
| E5 | What do placeholders do to identifier matching? | false merges per 10,000 for B0 and B5 at placeholder shares 0, 0.1, 0.2, 0.3, 0.4 |
| E6 | Are hard negatives kept apart? | LINK and REVIEW rates per hard negative category |
| E7 | Is performance equal across name origin groups and script pairs? | found and LINK recall per stratum with counts and intervals |
| E8 | How much does performance drop on the independent generator? | G1 minus G2 per system |
| E9 | What does review cost and save? | workload, residual error with a simulated reviewer, cost sweeps, break even against doing nothing |

## Analysis rules fixed in advance

- No method, threshold, guard or cost is changed after the first evaluation run. A needed
  change is recorded as a dated amendment below, keeping the original text.
- Every prediction is judged mechanically from the results files; misses are kept.
- The gold set (`data/gold/gold_pairs.jsonl`, author build_agent, not independent) is a smoke
  test and a reading aid, never a headline claim.

## Amendments

None yet.
