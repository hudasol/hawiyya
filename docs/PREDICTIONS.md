# Predictions

Registered before any experiment run (see `docs/PREREGISTRATION.md`). Rendered from
`spec/predictions.json` by `hawiyya docs build`; do not edit by hand. Each prediction is
judged mechanically in `docs/EVALUATION.md`.

| ID | Experiment | Prediction | Result file pointer | Threshold |
| --- | --- | --- | --- | --- |
| P-E1-1 | E1 | G1 pair completeness is at least 0.98. | `/generators/G1/pair_completeness/mean` | >= 0.98 |
| P-E1-2 | E1 | G2 pair completeness lies between 0.85 and 0.97 (lower than G1). | `/generators/G2/pair_completeness/mean` | between 0.85 and 0.97 |
| P-E1-3 | E1 | The block cap costs at most 0.005 of pair completeness on G1. | `/generators/G1/pc_lost_to_cap/mean` | <= 0.005 |
| P-E1-4 | E1 | G1 reduction ratio is at least 0.99. | `/generators/G1/reduction_ratio/mean` | >= 0.99 |
| P-E2-1 | E2 | Hawiyya makes at most 5 false merges per 10,000 records. | `/systems/B5_hawiyya/false_merges_per_10k/mean` | <= 5 |
| P-E2-2 | E2 | Hawiyya's automatic LINKs have precision of at least 0.995. | `/systems/B5_hawiyya/link_precision/mean` | >= 0.995 |
| P-E2-3 | E2 | Hawiyya finds (LINK or REVIEW) at least 95 percent of true pairs. | `/systems/B5_hawiyya/found_recall/mean` | >= 0.95 |
| P-E2-4 | E2 | Exact identifier matching makes at least 1,000 false merges per 10,000 records because unrelated people share placeholders. | `/systems/B0_eid_exact/false_merges_per_10k/mean` | >= 1000 |
| P-E2-5 | E2 | Exact name and date matching recalls at most 35 percent of true pairs. | `/systems/B1_name_dob_exact/link_recall/mean` | <= 0.35 |
| P-E2-6 | E2 | Hawiyya makes fewer false merges than its own forced (no review) variant. | `/systems/B5_hawiyya/false_merges_per_10k/mean` | < `/systems/B4_forced/false_merges_per_10k/mean` |
| P-E2-7 | E2 | The supervised reference makes at most 10 false merges per 10,000 records. | `/systems/B6_gbm/false_merges_per_10k/mean` | <= 10 |
| P-E2-8 | E2 | Removing Arabic and skeleton handling lowers found recall. | `/systems/B3_latin_only/found_recall/mean` | < `/systems/B5_hawiyya/found_recall/mean` |
| P-E2-9 | E2 | Hawiyya sends between 20 and 200 pairs to review per 1,000 records. | `/systems/B5_hawiyya/review_rate/mean` | between 20 and 200 |
| P-E3-1 | E3 | Expected calibration error is at most 0.01. | `/ece/mean` | <= 0.01 |
| P-E3-2 | E3 | Automatic LINK precision is at least 0.995. | `/auto_link_precision/mean` | >= 0.995 |
| P-E3-3 | E3 | Between 2 and 20 percent of candidate pairs go to review. | `/review_share/mean` | between 0.02 and 0.2 |
| P-E4-1 | E4 | Arabizi is the hardest name style (lowest found recall). | `/by_style` | lowest found_recall/rate is `arabizi` |
| P-E4-2 | E4 | Arabizi found recall is at least 0.05 below card read bilingual records. | `/by_style/arabizi/found_recall/rate` | `/by_style/bilingual_card/found_recall/rate` minus this >= 0.05 |
| P-E5-1 | E5 | With no placeholders, exact identifier matching has LINK precision of at least 0.98. | `/levels/0.0/B0_eid_exact/link_precision/mean` | >= 0.98 |
| P-E5-2 | E5 | With no placeholders, exact identifier matching reaches an F1 at least as high as Hawiyya's automatic LINKs (the simple baseline wins on clean records). | `/levels/0.0/B0_eid_exact/link_f1/mean` | >= `/levels/0.0/B5_hawiyya/link_f1/mean` |
| P-E5-3 | E5 | At a 40 percent placeholder share exact identifier matching makes at least 1,000 false merges per 10,000 records. | `/levels/0.4/B0_eid_exact/false_merges_per_10k/mean` | >= 1000 |
| P-E5-4 | E5 | At a 40 percent placeholder share Hawiyya makes at most 10 false merges per 10,000 records. | `/levels/0.4/B5_hawiyya/false_merges_per_10k/mean` | <= 10 |
| P-E6-1 | E6 | Hawiyya links at most 1 percent of twin pairs. | `/categories/twin/B5_hawiyya/link_rate/rate` | <= 0.01 |
| P-E6-2 | E6 | Hawiyya links at most 1 percent of same name father and son pairs. | `/categories/father_son_same_name/B5_hawiyya/link_rate/rate` | <= 0.01 |
| P-E6-3 | E6 | Hawiyya links at most 1 percent of newborn and mother pairs sharing an identifier. | `/categories/newborn_mother_shared_id/B5_hawiyya/link_rate/rate` | <= 0.01 |
| P-E6-4 | E6 | Exact identifier matching links at least 99 percent of newborn and mother pairs sharing an identifier. | `/categories/newborn_mother_shared_id/B0_eid_exact/link_rate/rate` | >= 0.99 |
| P-E6-5 | E6 | The forced variant links siblings at least as often as Hawiyya. | `/categories/sibling/B4_forced/link_rate/rate` | >= `/categories/sibling/B5_hawiyya/link_rate/rate` |
| P-E7-1 | E7 | Found recall differs by at most 0.05 between name origin groups. | `/by_origin` | max minus min of found_recall/rate <= 0.05 |
| P-E7-2 | E7 | Gulf Arab names have the lowest found recall. | `/by_origin` | lowest found_recall/rate is `gulf_arab` |
| P-E8-1 | E8 | Hawiyya's found recall drops by between 0.05 and 0.30 from G1 to G2. | `/systems/B5_hawiyya/drop_found_recall` | between 0.05 and 0.3 |
| P-E8-2 | E8 | Exact identifier matching's recall drops by at most 0.05 from G1 to G2. | `/systems/B0_eid_exact/drop_found_recall` | <= 0.05 |
| P-E8-3 | E8 | Calibration error is higher on G2 than on G1. | `/ece/G1` | < `/ece/G2` |
| P-E9-1 | E9 | With a perfect reviewer, Hawiyya's total cost is below the cost of doing nothing. | `/default/cost_hawiyya_perfect_reviewer` | < `/default/cost_do_nothing` |
| P-E9-2 | E9 | Between 10 and 150 review cases arise per 1,000 records. | `/default/reviews_per_1000` | between 10 and 150 |
| P-E9-3 | E9 | Raising the false merge cost from 500 to 2,000 raises the review rate. | `/sweeps/c_fm/500/review_rate` | < `/sweeps/c_fm/2000/review_rate` |
| P-H-1 | headline | On Tier M, Hawiyya makes at most 5 false merges per 10,000 records. | `/systems/B5_hawiyya/false_merges_per_10k/mean` | <= 5 |
| P-H-2 | headline | On Tier M, Hawiyya finds at least 93 percent of true pairs. | `/systems/B5_hawiyya/found_recall/mean` | >= 0.93 |
