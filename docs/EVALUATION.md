# Evaluation

All patients are synthetic. Every number below is generated from `results/experiments/` by
`hawiyya docs build` (the tables and the prediction verdicts are generated blocks; a test
re renders them and fails if they differ). The protocol, seeds and systems are in
`docs/PREREGISTRATION.md`; the predictions in `docs/PREDICTIONS.md` were committed before any
run. The generator and the method share an author (see the preregistration).

## Sealed run

<!-- BEGIN:sealed_record -->
The sealed run happened once, at commit `825bb3fe2e988476ad1c76044cf156d3fea82195`, started 2026-10-18T11:04:12Z and finished 2026-10-18T11:22:39Z (UTC). Seeds: {'g1': [1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009, 1010, 1011, 1012, 1013, 1014, 1015, 1016, 1017, 1018, 1019, 1020], 'g2': [1021, 1022, 1023, 1024, 1025, 1026, 1027, 1028, 1029, 1030], 'e5': [1001, 1002, 1003, 1004, 1005], 'sweep': [1001, 1002, 1003, 1004, 1005], 'headline': []}.
<!-- END:sealed_record -->

## Predictions, hits and misses

Each prediction is judged mechanically on the development seeds and on the sealed seeds.
Misses are kept.

<!-- BEGIN:predictions -->
| ID | Prediction | Development | Result | Sealed | Result |
| --- | --- | --- | --- | --- | --- |
| P-E1-1 | G1 pair completeness is at least 0.98. | 0.993514 | HIT | 0.993945 | HIT |
| P-E1-2 | G2 pair completeness lies between 0.85 and 0.97 (lower than G1). | 0.978316 | MISS | 0.979894 | MISS |
| P-E1-3 | The block cap costs at most 0.005 of pair completeness on G1. | 0.000581 | HIT | 0.000579 | HIT |
| P-E1-4 | G1 reduction ratio is at least 0.99. | 0.9982 | HIT | 0.998196 | HIT |
| P-E2-1 | Hawiyya makes at most 5 false merges per 10,000 records. | 0.042398 | HIT | 0 | HIT |
| P-E2-2 | Hawiyya's automatic LINKs have precision of at least 0.995. | 0.999994 | HIT | 1 | HIT |
| P-E2-3 | Hawiyya finds (LINK or REVIEW) at least 95 percent of true pairs. | 0.990683 | HIT | 0.991323 | HIT |
| P-E2-4 | Exact identifier matching makes at least 1,000 false merges per 10,000 records because unrelated people share placeholders. | 147698 | HIT | 152364 | HIT |
| P-E2-5 | Exact name and date matching recalls at most 35 percent of true pairs. | 0.097717 | HIT | 0.097538 | HIT |
| P-E2-6 | Hawiyya makes fewer false merges than its own forced (no review) variant. | 0.042398 vs 138.564 | HIT | 0 vs 137.478 | HIT |
| P-E2-7 | The supervised reference makes at most 10 false merges per 10,000 records. | 1.27805 | HIT | 0.857195 | HIT |
| P-E2-8 | Removing Arabic and skeleton handling lowers found recall. | 0.9888 vs 0.990683 | HIT | 0.989302 vs 0.991323 | HIT |
| P-E2-9 | Hawiyya sends between 20 and 200 pairs to review per 1,000 records. | 228.568 | MISS | 228.774 | MISS |
| P-E3-1 | Expected calibration error is at most 0.01. | 0.000446 | HIT | 0.000454 | HIT |
| P-E3-2 | Automatic LINK precision is at least 0.995. | 0.999994 | HIT | 1 | HIT |
| P-E3-3 | Between 2 and 20 percent of candidate pairs go to review. | 0.02162 | HIT | 0.021627 | HIT |
| P-E4-1 | Arabizi is the hardest name style (lowest found recall). | lowest: formal_translit | MISS | lowest: formal_translit | MISS |
| P-E4-2 | Arabizi found recall is at least 0.05 below card read bilingual records. | 0.992554 vs 0.994816 | MISS | 0.99294 vs 0.995207 | MISS |
| P-E5-1 | With no placeholders, exact identifier matching has LINK precision of at least 0.98. | 0.981841 | HIT | 0.979971 | MISS |
| P-E5-2 | With no placeholders, exact identifier matching reaches an F1 at least as high as Hawiyya's automatic LINKs (the simple baseline wins on clean records). | 0.916651 vs 0.953092 | MISS | 0.918087 vs 0.952037 | MISS |
| P-E5-3 | At a 40 percent placeholder share exact identifier matching makes at least 1,000 false merges per 10,000 records. | 3.92673e+06 | HIT | 3.8857e+06 | HIT |
| P-E5-4 | At a 40 percent placeholder share Hawiyya makes at most 10 false merges per 10,000 records. | 0 | HIT | 0.513904 | HIT |
| P-E6-1 | Hawiyya links at most 1 percent of twin pairs. | 0.000203 | HIT | 0 | HIT |
| P-E6-2 | Hawiyya links at most 1 percent of same name father and son pairs. | 0 | HIT | 0 | HIT |
| P-E6-3 | Hawiyya links at most 1 percent of newborn and mother pairs sharing an identifier. | 0 | HIT | 0 | HIT |
| P-E6-4 | Exact identifier matching links at least 99 percent of newborn and mother pairs sharing an identifier. | 1 | HIT | 1 | HIT |
| P-E6-5 | The forced variant links siblings at least as often as Hawiyya. | 0.010427 vs 0 | HIT | 0.010792 vs 0 | HIT |
| P-E7-1 | Found recall differs by at most 0.05 between name origin groups. | range 0.0068 | HIT | range 0.0071 | HIT |
| P-E7-2 | Gulf Arab names have the lowest found recall. | lowest: other_arab | MISS | lowest: other_arab | MISS |
| P-E8-1 | Hawiyya's found recall drops by between 0.05 and 0.30 from G1 to G2. | 0.024981 | MISS | 0.02285 | MISS |
| P-E8-2 | Exact identifier matching's recall drops by at most 0.05 from G1 to G2. | 0.046156 | HIT | 0.043483 | HIT |
| P-E8-3 | Calibration error is higher on G2 than on G1. | 0.000446 vs 0.002224 | HIT | 0.000454 vs 0.002335 | HIT |
| P-E9-1 | With a perfect reviewer, Hawiyya's total cost is below the cost of doing nothing. | 633.637 vs 18059.1 | HIT | 615.987 vs 17876.4 | HIT |
| P-E9-2 | Between 10 and 150 review cases arise per 1,000 records. | 233.686 | MISS | 231.526 | MISS |
| P-E9-3 | Raising the false merge cost from 500 to 2,000 raises the review rate. | 233.686 vs 247.459 | HIT | 231.526 vs 247.055 | HIT |
| P-H-1 | On Tier M, Hawiyya makes at most 5 false merges per 10,000 records. | 0.212527 | HIT | not run | not run |
| P-H-2 | On Tier M, Hawiyya finds at least 93 percent of true pairs. | 0.988895 | HIT | not run | not run |

- dev: 29 hits out of 37 judged predictions.
- sealed: 26 hits out of 35 judged predictions.
<!-- END:predictions -->

## Discussion

Written after the results; see the section below the tables.

## Development results

<!-- BEGIN:dev_tables -->
### E1 blocking (dev)

| Generator | Pair completeness | Lost to the cap | Reduction ratio | Pairs per record |
| --- | --- | --- | --- | --- |
| G1 | 0.9935 [0.9931, 0.9939] | 0.0006 [0.0004, 0.0008] | 0.998200 [0.998178, 0.998223] | 10.58 [10.44, 10.72] |
| G2 | 0.9783 [0.9769, 0.9797] | 0.0009 [0.0006, 0.0011] | 0.998296 [0.998264, 0.998328] | 9.99 [9.80, 10.17] |

### E2 systems on G1 (dev; mean [95% interval] over 20 seeds)

| System | LINK precision | LINK recall | LINK F1 | False merges per 10k | Found recall | Reviews per 1k | B3 precision | B3 recall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B0 identifier exact | 0.0428 [0.0417, 0.0440] | 0.7314 [0.7294, 0.7333] | 0.0809 [0.0789, 0.0830] | 147698.2 [143925.8, 151470.6] | 0.7314 [0.7294, 0.7333] | 0.0 [0.0, 0.0] | 0.9165 [0.9157, 0.9174] | 0.8457 [0.8445, 0.8468] |
| B1 name and date exact | 0.9995 [0.9990, 0.9999] | 0.0977 [0.0962, 0.0992] | 0.1780 [0.1755, 0.1805] | 0.5 [0.1, 0.8] | 0.0977 [0.0962, 0.0992] | 0.0 [0.0, 0.0] | 1.0000 [0.9999, 1.0000] | 0.4845 [0.4830, 0.4861] |
| B2 fuzzy raw names | 0.9973 [0.9966, 0.9981] | 0.1565 [0.1546, 0.1584] | 0.2705 [0.2676, 0.2734] | 3.7 [2.7, 4.8] | 0.1565 [0.1546, 0.1584] | 0.0 [0.0, 0.0] | 0.9997 [0.9996, 0.9998] | 0.5254 [0.5233, 0.5274] |
| B3 Hawiyya, Latin only | 1.0000 [1.0000, 1.0000] | 0.7953 [0.7934, 0.7972] | 0.8860 [0.8848, 0.8872] | 0.1 [-0.0, 0.2] | 0.9888 [0.9882, 0.9894] | 221.3 [218.1, 224.6] | 1.0000 [1.0000, 1.0000] | 0.8966 [0.8954, 0.8978] |
| B4 Hawiyya, forced (no review) | 0.9845 [0.9832, 0.9859] | 0.9771 [0.9762, 0.9781] | 0.9808 [0.9801, 0.9815] | 138.6 [126.1, 151.1] | 0.9771 [0.9762, 0.9781] | 0.0 [0.0, 0.0] | 0.9840 [0.9829, 0.9852] | 0.9928 [0.9923, 0.9932] |
| B5 Hawiyya (product) | 1.0000 [1.0000, 1.0000] | 0.7933 [0.7909, 0.7957] | 0.8847 [0.8832, 0.8862] | 0.0 [-0.0, 0.1] | 0.9907 [0.9903, 0.9911] | 228.6 [225.1, 232.1] | 1.0000 [1.0000, 1.0000] | 0.8939 [0.8923, 0.8956] |
| B6 supervised reference | 0.9998 [0.9998, 0.9999] | 0.9356 [0.9342, 0.9370] | 0.9666 [0.9659, 0.9674] | 1.3 [0.7, 1.8] | 0.9917 [0.9913, 0.9921] | 70.8 [69.0, 72.6] | 0.9999 [0.9998, 0.9999] | 0.9741 [0.9734, 0.9749] |

Where a baseline beats the product:

- B0 identifier exact beats the product on Reviews per 1k (0.0 against 228.6).
- B1 name and date exact beats the product on Reviews per 1k (0.0 against 228.6).
- B2 fuzzy raw names beats the product on Reviews per 1k (0.0 against 228.6).
- B3 Hawiyya, Latin only beats the product on LINK recall (0.7953 against 0.7933).
- B3 Hawiyya, Latin only beats the product on LINK F1 (0.8860 against 0.8847).
- B3 Hawiyya, Latin only beats the product on Reviews per 1k (221.3 against 228.6).
- B3 Hawiyya, Latin only beats the product on B3 recall (0.8966 against 0.8939).
- B4 Hawiyya, forced (no review) beats the product on LINK recall (0.9771 against 0.7933).
- B4 Hawiyya, forced (no review) beats the product on LINK F1 (0.9808 against 0.8847).
- B4 Hawiyya, forced (no review) beats the product on Reviews per 1k (0.0 against 228.6).
- B4 Hawiyya, forced (no review) beats the product on B3 recall (0.9928 against 0.8939).
- B6 supervised reference beats the product on LINK recall (0.9356 against 0.7933).
- B6 supervised reference beats the product on LINK F1 (0.9666 against 0.8847).
- B6 supervised reference beats the product on Found recall (0.9917 against 0.9907).
- B6 supervised reference beats the product on Reviews per 1k (70.8 against 228.6).
- B6 supervised reference beats the product on B3 recall (0.9741 against 0.8939).

### E3 calibration and abstention (dev)

- Expected calibration error: 0.0004 [0.0004, 0.0005]
- Precision of automatic LINKs: 1.0000 [1.0000, 1.0000]
- Share of candidate pairs sent to review: 0.0216 [0.0212, 0.0220]
- Estimation (fitting seeds): lambda plain EM 0.161872, anchored 0.085327, labels 0.083595; average precision plain EM 0.959849, anchored 0.999135, labels 0.999218.

| Probability bin | Pairs | Mean predicted | Observed |
| --- | --- | --- | --- |
| 0.0 | 2265932 | 0.000277 | 0.000265 |
| 0.1 | 4019 | 0.13792 | 0.121423 |
| 0.2 | 3336 | 0.25993 | 0.229317 |
| 0.3 | 2451 | 0.373466 | 0.340677 |
| 0.4 | 1719 | 0.4559 | 0.453752 |
| 0.5 | 2251 | 0.574124 | 0.587739 |
| 0.6 | 1242 | 0.690371 | 0.670692 |
| 0.7 | 3408 | 0.769911 | 0.770246 |
| 0.8 | 2546 | 0.862731 | 0.856638 |
| 0.9 | 200922 | 0.996449 | 0.996148 |

| Coverage (share of candidates, highest probability first) | Precision |
| --- | --- |
| 0.01 | 1.0000 |
| 0.02 | 1.0000 |
| 0.05 | 1.0000 |
| 0.1 | 0.8468 |
| 0.2 | 0.4235 |
| 0.3 | 0.2823 |
| 0.5 | 0.1694 |
| 0.75 | 0.1129 |
| 1.0 | 0.0847 |

### E4 found recall by name style and corruption (dev, pooled, Wilson 95%)

| Stratum | Found recall |
| --- | --- |
| style arabizi | 0.9926 [0.9918, 0.9932] (n=60567) |
| style bilingual_card | 0.9948 [0.9943, 0.9953] (n=83909) |
| style formal_ar | 0.9919 [0.9912, 0.9926] (n=65774) |
| style formal_translit | 0.9821 [0.9802, 0.9838] (n=21349) |
| style gulf | 0.9921 [0.9914, 0.9927] (n=71646) |
| style variant_en | 0.9875 [0.9868, 0.9881] (n=105780) |
| corruption name:ar_swap | 0.9602 [0.9534, 0.9660] (n=3693) |
| corruption name:ar_typo | 0.9864 [0.9813, 0.9902] (n=2651) |
| corruption name:bin | 0.9910 [0.9896, 0.9923] (n=18650) |
| corruption name:drop_father | 0.9870 [0.9854, 0.9885] (n=20608) |
| corruption name:honorific | 0.9885 [0.9862, 0.9903] (n=10304) |
| corruption name:initial | 0.9869 [0.9840, 0.9893] (n=7029) |
| corruption name:swap | 0.9342 [0.9299, 0.9382] (n=13701) |
| corruption name:typo | 0.9813 [0.9794, 0.9831] (n=20235) |

### E5 placeholder share (dev)

| Share | System | LINK precision | LINK F1 | False merges per 10k |
| --- | --- | --- | --- | --- |
| 0.0 | B0 identifier exact | 0.9818 [0.9793, 0.9844] | 0.9167 [0.9112, 0.9221] | 142.3 [123.2, 161.5] |
| 0.0 | B4 Hawiyya, forced (no review) | 0.9896 [0.9857, 0.9935] | 0.9893 [0.9870, 0.9917] | 92.8 [57.5, 128.2] |
| 0.0 | B5 Hawiyya (product) | 1.0000 [1.0000, 1.0000] | 0.9531 [0.9495, 0.9567] | 0.0 [0.0, 0.0] |
| 0.1 | B0 identifier exact | 0.0255 [0.0225, 0.0284] | 0.0491 [0.0437, 0.0545] | 243929.7 [217206.5, 270652.8] |
| 0.1 | B4 Hawiyya, forced (no review) | 0.9824 [0.9800, 0.9849] | 0.9802 [0.9788, 0.9816] | 157.2 [134.6, 179.7] |
| 0.1 | B5 Hawiyya (product) | 1.0000 [1.0000, 1.0000] | 0.8699 [0.8639, 0.8759] | 0.0 [0.0, 0.0] |
| 0.2 | B0 identifier exact | 0.0053 [0.0049, 0.0057] | 0.0105 [0.0097, 0.0112] | 959843.4 [902445.8, 1017241.0] |
| 0.2 | B4 Hawiyya, forced (no review) | 0.9778 [0.9735, 0.9821] | 0.9735 [0.9705, 0.9764] | 197.3 [157.3, 237.3] |
| 0.2 | B5 Hawiyya (product) | 1.0000 [1.0000, 1.0000] | 0.7817 [0.7701, 0.7933] | 0.0 [0.0, 0.0] |
| 0.3 | B0 identifier exact | 0.0019 [0.0018, 0.0019] | 0.0037 [0.0036, 0.0039] | 2221753.3 [2119039.3, 2324467.4] |
| 0.3 | B4 Hawiyya, forced (no review) | 0.9710 [0.9682, 0.9737] | 0.9661 [0.9630, 0.9693] | 257.8 [233.0, 282.6] |
| 0.3 | B5 Hawiyya (product) | 1.0000 [1.0000, 1.0000] | 0.6960 [0.6881, 0.7038] | 0.0 [0.0, 0.0] |
| 0.4 | B0 identifier exact | 0.0009 [0.0008, 0.0009] | 0.0017 [0.0017, 0.0018] | 3926731.2 [3790698.3, 4062764.2] |
| 0.4 | B4 Hawiyya, forced (no review) | 0.9680 [0.9660, 0.9700] | 0.9595 [0.9574, 0.9616] | 281.9 [263.3, 300.5] |
| 0.4 | B5 Hawiyya (product) | 1.0000 [1.0000, 1.0000] | 0.6005 [0.5863, 0.6147] | 0.0 [0.0, 0.0] |

### E6 hard negatives (dev, pooled pairs, Wilson 95%)

| Category | System | LINK rate | REVIEW rate |
| --- | --- | --- | --- |
| cousin | B0 identifier exact | 0.0545 [0.0512, 0.0581] (n=16447) | 0.0000 [0.0000, 0.0002] (n=16447) |
| cousin | B4 Hawiyya, forced (no review) | 0.0001 [0.0000, 0.0004] (n=16447) | 0.0000 [0.0000, 0.0002] (n=16447) |
| cousin | B5 Hawiyya (product) | 0.0000 [0.0000, 0.0002] (n=16447) | 0.0009 [0.0006, 0.0015] (n=16447) |
| father_son_same_name | B0 identifier exact | 0.0018 [0.0009, 0.0038] (n=3808) | 0.0000 [0.0000, 0.0010] (n=3808) |
| father_son_same_name | B4 Hawiyya, forced (no review) | 0.0144 [0.0111, 0.0188] (n=3808) | 0.0000 [0.0000, 0.0010] (n=3808) |
| father_son_same_name | B5 Hawiyya (product) | 0.0000 [0.0000, 0.0010] (n=3808) | 0.0604 [0.0533, 0.0684] (n=3808) |
| newborn_mother_shared_id | B0 identifier exact | 1.0000 [0.9986, 1.0000] (n=2678) | 0.0000 [0.0000, 0.0014] (n=2678) |
| newborn_mother_shared_id | B4 Hawiyya, forced (no review) | 0.0000 [0.0000, 0.0014] (n=2678) | 0.0000 [0.0000, 0.0014] (n=2678) |
| newborn_mother_shared_id | B5 Hawiyya (product) | 0.0000 [0.0000, 0.0014] (n=2678) | 0.0026 [0.0013, 0.0054] (n=2678) |
| other_nonmatch | B0 identifier exact | 0.0000 [0.0000, 0.0000] (n=2065005) | 0.0000 [0.0000, 0.0000] (n=2065005) |
| other_nonmatch | B4 Hawiyya, forced (no review) | 0.0000 [0.0000, 0.0000] (n=2065005) | 0.0000 [0.0000, 0.0000] (n=2065005) |
| other_nonmatch | B5 Hawiyya (product) | 0.0000 [0.0000, 0.0000] (n=2065005) | 0.0008 [0.0008, 0.0009] (n=2065005) |
| parent_child | B0 identifier exact | 0.0099 [0.0093, 0.0106] (n=88016) | 0.0000 [0.0000, 0.0000] (n=88016) |
| parent_child | B4 Hawiyya, forced (no review) | 0.0049 [0.0045, 0.0054] (n=88016) | 0.0000 [0.0000, 0.0000] (n=88016) |
| parent_child | B5 Hawiyya (product) | 0.0000 [0.0000, 0.0000] (n=88016) | 0.0292 [0.0281, 0.0303] (n=88016) |
| same_dob_sex | B0 identifier exact | 0.0000 [0.0000, 0.0026] (n=1496) | 0.0000 [0.0000, 0.0026] (n=1496) |
| same_dob_sex | B4 Hawiyya, forced (no review) | 0.0107 [0.0066, 0.0173] (n=1496) | 0.0000 [0.0000, 0.0026] (n=1496) |
| same_dob_sex | B5 Hawiyya (product) | 0.0000 [0.0000, 0.0026] (n=1496) | 0.0140 [0.0092, 0.0214] (n=1496) |
| shared_placeholder | B0 identifier exact | 1.0000 [1.0000, 1.0000] (n=3467252) | 0.0000 [0.0000, 0.0000] (n=3467252) |
| shared_placeholder | B4 Hawiyya, forced (no review) | 0.0000 [0.0000, 0.0000] (n=3467252) | 0.0000 [0.0000, 0.0000] (n=3467252) |
| shared_placeholder | B5 Hawiyya (product) | 0.0000 [0.0000, 0.0000] (n=3467252) | 0.0000 [0.0000, 0.0000] (n=3467252) |
| sibling | B0 identifier exact | 0.0112 [0.0106, 0.0119] (n=90631) | 0.0000 [0.0000, 0.0000] (n=90631) |
| sibling | B4 Hawiyya, forced (no review) | 0.0104 [0.0098, 0.0111] (n=90631) | 0.0000 [0.0000, 0.0000] (n=90631) |
| sibling | B5 Hawiyya (product) | 0.0000 [0.0000, 0.0000] (n=90631) | 0.0460 [0.0446, 0.0473] (n=90631) |
| spouse | B0 identifier exact | 0.1443 [0.1255, 0.1653] (n=1199) | 0.0000 [0.0000, 0.0032] (n=1199) |
| spouse | B4 Hawiyya, forced (no review) | 0.0000 [0.0000, 0.0032] (n=1199) | 0.0000 [0.0000, 0.0032] (n=1199) |
| spouse | B5 Hawiyya (product) | 0.0000 [0.0000, 0.0032] (n=1199) | 0.0017 [0.0005, 0.0061] (n=1199) |
| twin | B0 identifier exact | 0.0124 [0.0096, 0.0159] (n=4928) | 0.0000 [0.0000, 0.0008] (n=4928) |
| twin | B4 Hawiyya, forced (no review) | 0.3513 [0.3381, 0.3647] (n=4928) | 0.0000 [0.0000, 0.0008] (n=4928) |
| twin | B5 Hawiyya (product) | 0.0002 [0.0000, 0.0011] (n=4928) | 0.6400 [0.6265, 0.6533] (n=4928) |

### E7 equity (dev, product, pooled true pairs, Wilson 95%)

| Stratum | Found recall | LINK recall |
| --- | --- | --- |
| origin gulf_arab | 0.9900 [0.9893, 0.9907] (n=71951) | 0.8336 [0.8308, 0.8363] (n=71951) |
| origin other_arab | 0.9885 [0.9874, 0.9895] (n=41923) | 0.7870 [0.7831, 0.7909] (n=41923) |
| origin south_asian | 0.9910 [0.9902, 0.9917] (n=58683) | 0.7569 [0.7534, 0.7604] (n=58683) |
| origin southeast_asian | 0.9928 [0.9917, 0.9938] (n=23581) | 0.7719 [0.7664, 0.7772] (n=23581) |
| origin western | 0.9953 [0.9941, 0.9963] (n=15814) | 0.7938 [0.7874, 0.8000] (n=15814) |
| scripts ar+ar | 0.9907 [0.9810, 0.9955] (n=756) | 0.8849 [0.8602, 0.9057] (n=756) |
| scripts ar+both | 0.9972 [0.9962, 0.9979] (n=16157) | 0.8930 [0.8881, 0.8977] (n=16157) |
| scripts ar+latin | 0.9902 [0.9893, 0.9911] (n=48861) | 0.7951 [0.7915, 0.7987] (n=48861) |
| scripts both+both | 1.0000 [0.9965, 1.0000] (n=1100) | 0.9345 [0.9184, 0.9477] (n=1100) |
| scripts both+latin | 0.9942 [0.9936, 0.9947] (n=66652) | 0.8346 [0.8318, 0.8374] (n=66652) |
| scripts latin+latin | 0.9865 [0.9857, 0.9873] (n=78426) | 0.7337 [0.7306, 0.7368] (n=78426) |

False merges by origin of the pair: {'other_arab': 1} (total 1).

### E8 independence: G1 against G2 (dev)

| System | Found recall G1 | Found recall G2 | Drop | LINK F1 G1 | LINK F1 G2 | False merges per 10k G1 | G2 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| B0 identifier exact | 0.7314 | 0.6852 | 0.0462 | 0.0809 | 0.0713 | 147698.2 | 157574.2 |
| B1 name and date exact | 0.0977 | 0.1999 | -0.1022 | 0.1780 | 0.3331 | 0.5 | 2.6 |
| B2 fuzzy raw names | 0.1565 | 0.1568 | -0.0003 | 0.2705 | 0.2709 | 3.7 | 3.3 |
| B3 Hawiyya, Latin only | 0.9888 | 0.9605 | 0.0283 | 0.8860 | 0.8355 | 0.1 | 0.0 |
| B4 Hawiyya, forced (no review) | 0.9771 | 0.9375 | 0.0396 | 0.9808 | 0.9608 | 138.6 | 125.2 |
| B5 Hawiyya (product) | 0.9907 | 0.9657 | 0.0250 | 0.8847 | 0.8328 | 0.0 | 0.0 |
| B6 supervised reference | 0.9917 | 0.9661 | 0.0256 | 0.9666 | 0.9251 | 1.3 | 1.3 |

Calibration error: G1 0.000446, G2 0.002224.

### E9 review economics (dev; per 1,000 records; costs in abstract cost units)

Costs: {'c_fm': 500.0, 'c_md': 20.0, 'c_r': 2.0}; simulated reviewer: {'accuracy': 0.97, 'minutes_per_case': 4.0}.

| Quantity | Value |
| --- | --- |
| reviews per 1000 | 233.686 |
| minutes per 1000 | 934.743 |
| residual false merges perfect per 1000 | 0.000 |
| residual missed perfect per 1000 | 8.313 |
| residual false merges reviewer per 1000 | 1.646 |
| residual missed reviewer per 1000 | 14.049 |
| cost hawiyya perfect reviewer | 633.637 |
| cost hawiyya reviewer | 1571.475 |
| cost do nothing | 18059.128 |

| Sweep | Value | Reviews per 1k | False merges per 10k | LINK recall | Found recall |
| --- | --- | --- | --- | --- | --- |
| c_fm | 50 | 161.2 | 0.17 | 0.8736 | 0.9908 |
| c_fm | 100 | 161.2 | 0.17 | 0.8736 | 0.9908 |
| c_fm | 250 | 164.9 | 0.17 | 0.8695 | 0.9908 |
| c_fm | 500 | 233.7 | 0.00 | 0.7933 | 0.9908 |
| c_fm | 1000 | 233.7 | 0.00 | 0.7933 | 0.9908 |
| c_fm | 2000 | 247.5 | 0.00 | 0.7781 | 0.9908 |
| c_fm | 5000 | 247.5 | 0.00 | 0.7781 | 0.9908 |
| c_md | 5 | 191.0 | 0.00 | 0.7933 | 0.9815 |
| c_md | 10 | 217.5 | 0.00 | 0.7933 | 0.9887 |
| c_md | 20 | 233.7 | 0.00 | 0.7933 | 0.9908 |
| c_md | 50 | 258.5 | 0.00 | 0.7933 | 0.9924 |
| c_md | 100 | 270.8 | 0.00 | 0.7933 | 0.9927 |
| c_r | 0.5 | 284.6 | 0.00 | 0.7781 | 0.9927 |
| c_r | 1 | 252.3 | 0.00 | 0.7933 | 0.9921 |
| c_r | 2 | 233.7 | 0.00 | 0.7933 | 0.9908 |
| c_r | 5 | 146.6 | 0.17 | 0.8695 | 0.9884 |
| c_r | 10 | 110.6 | 0.17 | 0.8736 | 0.9779 |

### Headline run, Tier M (dev, seeds [26, 27, 28, 29, 30])

| System | LINK precision | LINK recall | LINK F1 | False merges per 10k | Found recall | Reviews per 1k | B3 precision | B3 recall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B0 identifier exact | 0.0110 [0.0107, 0.0112] | 0.7321 [0.7291, 0.7351] | 0.0216 [0.0212, 0.0221] | 593296.5 [582759.2, 603833.9] | 0.7321 [0.7291, 0.7351] | 0.0 [0.0, 0.0] | 0.9160 [0.9152, 0.9168] | 0.8466 [0.8455, 0.8477] |
| B4 Hawiyya, forced (no review) | 0.9818 [0.9799, 0.9837] | 0.9766 [0.9757, 0.9775] | 0.9792 [0.9785, 0.9799] | 163.0 [145.5, 180.5] | 0.9766 [0.9757, 0.9775] | 0.0 [0.0, 0.0] | 0.9806 [0.9786, 0.9826] | 0.9926 [0.9921, 0.9931] |
| B5 Hawiyya (product) | 1.0000 [0.9999, 1.0000] | 0.7990 [0.7966, 0.8013] | 0.8882 [0.8868, 0.8897] | 0.2 [-0.1, 0.5] | 0.9889 [0.9885, 0.9893] | 230.6 [227.9, 233.4] | 1.0000 [0.9999, 1.0000] | 0.8980 [0.8969, 0.8990] |
<!-- END:dev_tables -->

## Sealed results

<!-- BEGIN:sealed_tables -->
### E1 blocking (sealed)

| Generator | Pair completeness | Lost to the cap | Reduction ratio | Pairs per record |
| --- | --- | --- | --- | --- |
| G1 | 0.9939 [0.9935, 0.9944] | 0.0006 [0.0004, 0.0007] | 0.998196 [0.998170, 0.998221] | 10.59 [10.44, 10.74] |
| G2 | 0.9799 [0.9788, 0.9810] | 0.0009 [0.0007, 0.0011] | 0.998310 [0.998275, 0.998344] | 9.93 [9.72, 10.14] |

### E2 systems on G1 (sealed; mean [95% interval] over 20 seeds)

| System | LINK precision | LINK recall | LINK F1 | False merges per 10k | Found recall | Reviews per 1k | B3 precision | B3 recall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B0 identifier exact | 0.0416 [0.0400, 0.0432] | 0.7319 [0.7292, 0.7345] | 0.0787 [0.0758, 0.0816] | 152363.8 [146671.4, 158056.3] | 0.7319 [0.7292, 0.7345] | 0.0 [0.0, 0.0] | 0.9155 [0.9142, 0.9168] | 0.8463 [0.8447, 0.8478] |
| B1 name and date exact | 0.9994 [0.9989, 1.0000] | 0.0975 [0.0961, 0.0990] | 0.1777 [0.1753, 0.1801] | 0.5 [-0.0, 1.0] | 0.0975 [0.0961, 0.0990] | 0.0 [0.0, 0.0] | 1.0000 [0.9999, 1.0000] | 0.4853 [0.4836, 0.4870] |
| B2 fuzzy raw names | 0.9978 [0.9968, 0.9987] | 0.1572 [0.1551, 0.1593] | 0.2716 [0.2685, 0.2747] | 3.1 [1.8, 4.4] | 0.1572 [0.1551, 0.1593] | 0.0 [0.0, 0.0] | 0.9997 [0.9996, 0.9998] | 0.5267 [0.5247, 0.5287] |
| B3 Hawiyya, Latin only | 1.0000 [1.0000, 1.0000] | 0.7949 [0.7920, 0.7978] | 0.8857 [0.8839, 0.8875] | 0.0 [-0.0, 0.1] | 0.9893 [0.9886, 0.9900] | 221.1 [218.2, 224.1] | 1.0000 [1.0000, 1.0000] | 0.8959 [0.8945, 0.8973] |
| B4 Hawiyya, forced (no review) | 0.9846 [0.9837, 0.9854] | 0.9776 [0.9768, 0.9784] | 0.9811 [0.9805, 0.9817] | 137.5 [130.1, 144.9] | 0.9776 [0.9768, 0.9784] | 0.0 [0.0, 0.0] | 0.9832 [0.9825, 0.9839] | 0.9929 [0.9925, 0.9933] |
| B5 Hawiyya (product) | 1.0000 [1.0000, 1.0000] | 0.7921 [0.7893, 0.7950] | 0.8840 [0.8822, 0.8858] | 0.0 [0.0, 0.0] | 0.9913 [0.9908, 0.9918] | 228.8 [225.6, 232.0] | 1.0000 [1.0000, 1.0000] | 0.8930 [0.8915, 0.8944] |
| B6 supervised reference | 0.9999 [0.9998, 1.0000] | 0.9361 [0.9341, 0.9382] | 0.9670 [0.9658, 0.9681] | 0.9 [0.3, 1.4] | 0.9922 [0.9917, 0.9927] | 70.2 [68.0, 72.4] | 0.9999 [0.9998, 0.9999] | 0.9742 [0.9733, 0.9751] |

Where a baseline beats the product:

- B0 identifier exact beats the product on Reviews per 1k (0.0 against 228.8).
- B1 name and date exact beats the product on Reviews per 1k (0.0 against 228.8).
- B2 fuzzy raw names beats the product on Reviews per 1k (0.0 against 228.8).
- B3 Hawiyya, Latin only beats the product on LINK recall (0.7949 against 0.7921).
- B3 Hawiyya, Latin only beats the product on LINK F1 (0.8857 against 0.8840).
- B3 Hawiyya, Latin only beats the product on Reviews per 1k (221.1 against 228.8).
- B3 Hawiyya, Latin only beats the product on B3 recall (0.8959 against 0.8930).
- B4 Hawiyya, forced (no review) beats the product on LINK recall (0.9776 against 0.7921).
- B4 Hawiyya, forced (no review) beats the product on LINK F1 (0.9811 against 0.8840).
- B4 Hawiyya, forced (no review) beats the product on Reviews per 1k (0.0 against 228.8).
- B4 Hawiyya, forced (no review) beats the product on B3 recall (0.9929 against 0.8930).
- B6 supervised reference beats the product on LINK recall (0.9361 against 0.7921).
- B6 supervised reference beats the product on LINK F1 (0.9670 against 0.8840).
- B6 supervised reference beats the product on Found recall (0.9922 against 0.9913).
- B6 supervised reference beats the product on Reviews per 1k (70.2 against 228.8).
- B6 supervised reference beats the product on B3 recall (0.9742 against 0.8930).

### E3 calibration and abstention (sealed)

- Expected calibration error: 0.0005 [0.0004, 0.0005]
- Precision of automatic LINKs: 1.0000 [1.0000, 1.0000]
- Share of candidate pairs sent to review: 0.0216 [0.0212, 0.0220]
- Estimation (fitting seeds): lambda plain EM 0.161872, anchored 0.085327, labels 0.083595; average precision plain EM 0.959849, anchored 0.999135, labels 0.999218.

| Probability bin | Pairs | Mean predicted | Observed |
| --- | --- | --- | --- |
| 0.0 | 2264338 | 0.000268 | 0.000244 |
| 0.1 | 3946 | 0.136634 | 0.118348 |
| 0.2 | 3301 | 0.260211 | 0.241442 |
| 0.3 | 2427 | 0.373674 | 0.356819 |
| 0.4 | 1699 | 0.45613 | 0.447911 |
| 0.5 | 2316 | 0.574124 | 0.588515 |
| 0.6 | 1179 | 0.690164 | 0.675997 |
| 0.7 | 3509 | 0.76978 | 0.768595 |
| 0.8 | 2407 | 0.862934 | 0.855006 |
| 0.9 | 199904 | 0.996494 | 0.996353 |

| Coverage (share of candidates, highest probability first) | Precision |
| --- | --- |
| 0.01 | 1.0000 |
| 0.02 | 1.0000 |
| 0.05 | 1.0000 |
| 0.1 | 0.8436 |
| 0.2 | 0.4219 |
| 0.3 | 0.2813 |
| 0.5 | 0.1688 |
| 0.75 | 0.1125 |
| 1.0 | 0.0844 |

### E4 found recall by name style and corruption (sealed, pooled, Wilson 95%)

| Stratum | Found recall |
| --- | --- |
| style arabizi | 0.9929 [0.9922, 0.9936] (n=60338) |
| style bilingual_card | 0.9952 [0.9947, 0.9957] (n=83871) |
| style formal_ar | 0.9919 [0.9912, 0.9926] (n=65547) |
| style formal_translit | 0.9835 [0.9817, 0.9851] (n=21467) |
| style gulf | 0.9923 [0.9916, 0.9929] (n=70981) |
| style variant_en | 0.9887 [0.9881, 0.9894] (n=104844) |
| corruption name:ar_swap | 0.9562 [0.9490, 0.9625] (n=3540) |
| corruption name:ar_typo | 0.9893 [0.9846, 0.9925] (n=2702) |
| corruption name:bin | 0.9918 [0.9904, 0.9930] (n=18006) |
| corruption name:drop_father | 0.9878 [0.9862, 0.9892] (n=20817) |
| corruption name:honorific | 0.9904 [0.9883, 0.9921] (n=10207) |
| corruption name:initial | 0.9837 [0.9804, 0.9864] (n=6919) |
| corruption name:swap | 0.9353 [0.9310, 0.9393] (n=13256) |
| corruption name:typo | 0.9853 [0.9836, 0.9869] (n=20064) |

### E5 placeholder share (sealed)

| Share | System | LINK precision | LINK F1 | False merges per 10k |
| --- | --- | --- | --- | --- |
| 0.0 | B0 identifier exact | 0.9800 [0.9724, 0.9875] | 0.9181 [0.9121, 0.9240] | 159.3 [96.8, 221.7] |
| 0.0 | B4 Hawiyya, forced (no review) | 0.9896 [0.9872, 0.9921] | 0.9883 [0.9862, 0.9905] | 93.0 [71.3, 114.7] |
| 0.0 | B5 Hawiyya (product) | 1.0000 [1.0000, 1.0000] | 0.9520 [0.9485, 0.9556] | 0.0 [0.0, 0.0] |
| 0.1 | B0 identifier exact | 0.0250 [0.0246, 0.0254] | 0.0484 [0.0476, 0.0491] | 246019.1 [240730.8, 251307.5] |
| 0.1 | B4 Hawiyya, forced (no review) | 0.9835 [0.9818, 0.9852] | 0.9810 [0.9804, 0.9816] | 147.6 [131.3, 163.9] |
| 0.1 | B5 Hawiyya (product) | 1.0000 [1.0000, 1.0000] | 0.8682 [0.8648, 0.8717] | 0.0 [0.0, 0.0] |
| 0.2 | B0 identifier exact | 0.0051 [0.0048, 0.0055] | 0.0102 [0.0095, 0.0108] | 990051.8 [941675.8, 1038427.8] |
| 0.2 | B4 Hawiyya, forced (no review) | 0.9784 [0.9736, 0.9833] | 0.9745 [0.9716, 0.9774] | 193.1 [147.9, 238.2] |
| 0.2 | B5 Hawiyya (product) | 1.0000 [1.0000, 1.0000] | 0.7785 [0.7727, 0.7843] | 0.0 [0.0, 0.0] |
| 0.3 | B0 identifier exact | 0.0019 [0.0018, 0.0020] | 0.0037 [0.0036, 0.0039] | 2220674.5 [2132870.2, 2308478.9] |
| 0.3 | B4 Hawiyya, forced (no review) | 0.9739 [0.9714, 0.9764] | 0.9674 [0.9657, 0.9690] | 233.1 [208.7, 257.5] |
| 0.3 | B5 Hawiyya (product) | 1.0000 [1.0000, 1.0000] | 0.6892 [0.6839, 0.6944] | 0.0 [0.0, 0.0] |
| 0.4 | B0 identifier exact | 0.0009 [0.0008, 0.0009] | 0.0018 [0.0017, 0.0019] | 3885699.9 [3742586.8, 4028813.1] |
| 0.4 | B4 Hawiyya, forced (no review) | 0.9682 [0.9656, 0.9709] | 0.9610 [0.9583, 0.9637] | 281.2 [257.9, 304.6] |
| 0.4 | B5 Hawiyya (product) | 0.9999 [0.9996, 1.0001] | 0.6067 [0.5937, 0.6198] | 0.5 [-0.4, 1.5] |

### E6 hard negatives (sealed, pooled pairs, Wilson 95%)

| Category | System | LINK rate | REVIEW rate |
| --- | --- | --- | --- |
| cousin | B0 identifier exact | 0.0572 [0.0537, 0.0608] (n=16797) | 0.0000 [0.0000, 0.0002] (n=16797) |
| cousin | B4 Hawiyya, forced (no review) | 0.0002 [0.0001, 0.0005] (n=16797) | 0.0000 [0.0000, 0.0002] (n=16797) |
| cousin | B5 Hawiyya (product) | 0.0000 [0.0000, 0.0002] (n=16797) | 0.0010 [0.0006, 0.0016] (n=16797) |
| father_son_same_name | B0 identifier exact | 0.0018 [0.0009, 0.0036] (n=3956) | 0.0000 [0.0000, 0.0010] (n=3956) |
| father_son_same_name | B4 Hawiyya, forced (no review) | 0.0139 [0.0107, 0.0181] (n=3956) | 0.0000 [0.0000, 0.0010] (n=3956) |
| father_son_same_name | B5 Hawiyya (product) | 0.0000 [0.0000, 0.0010] (n=3956) | 0.0526 [0.0460, 0.0600] (n=3956) |
| newborn_mother_shared_id | B0 identifier exact | 1.0000 [0.9986, 1.0000] (n=2705) | 0.0000 [0.0000, 0.0014] (n=2705) |
| newborn_mother_shared_id | B4 Hawiyya, forced (no review) | 0.0000 [0.0000, 0.0014] (n=2705) | 0.0000 [0.0000, 0.0014] (n=2705) |
| newborn_mother_shared_id | B5 Hawiyya (product) | 0.0000 [0.0000, 0.0014] (n=2705) | 0.0018 [0.0008, 0.0043] (n=2705) |
| other_nonmatch | B0 identifier exact | 0.0000 [0.0000, 0.0000] (n=2064037) | 0.0000 [0.0000, 0.0000] (n=2064037) |
| other_nonmatch | B4 Hawiyya, forced (no review) | 0.0000 [0.0000, 0.0001] (n=2064037) | 0.0000 [0.0000, 0.0000] (n=2064037) |
| other_nonmatch | B5 Hawiyya (product) | 0.0000 [0.0000, 0.0000] (n=2064037) | 0.0008 [0.0007, 0.0008] (n=2064037) |
| parent_child | B0 identifier exact | 0.0098 [0.0092, 0.0105] (n=86987) | 0.0000 [0.0000, 0.0000] (n=86987) |
| parent_child | B4 Hawiyya, forced (no review) | 0.0049 [0.0044, 0.0053] (n=86987) | 0.0000 [0.0000, 0.0000] (n=86987) |
| parent_child | B5 Hawiyya (product) | 0.0000 [0.0000, 0.0000] (n=86987) | 0.0281 [0.0270, 0.0292] (n=86987) |
| same_dob_sex | B0 identifier exact | 0.0000 [0.0000, 0.0027] (n=1437) | 0.0000 [0.0000, 0.0027] (n=1437) |
| same_dob_sex | B4 Hawiyya, forced (no review) | 0.0118 [0.0074, 0.0189] (n=1437) | 0.0000 [0.0000, 0.0027] (n=1437) |
| same_dob_sex | B5 Hawiyya (product) | 0.0000 [0.0000, 0.0027] (n=1437) | 0.0334 [0.0253, 0.0440] (n=1437) |
| shared_placeholder | B0 identifier exact | 1.0000 [1.0000, 1.0000] (n=3569596) | 0.0000 [0.0000, 0.0000] (n=3569596) |
| shared_placeholder | B4 Hawiyya, forced (no review) | 0.0000 [0.0000, 0.0000] (n=3569596) | 0.0000 [0.0000, 0.0000] (n=3569596) |
| shared_placeholder | B5 Hawiyya (product) | 0.0000 [0.0000, 0.0000] (n=3569596) | 0.0000 [0.0000, 0.0000] (n=3569596) |
| sibling | B0 identifier exact | 0.0122 [0.0115, 0.0129] (n=90255) | 0.0000 [0.0000, 0.0000] (n=90255) |
| sibling | B4 Hawiyya, forced (no review) | 0.0108 [0.0101, 0.0115] (n=90255) | 0.0000 [0.0000, 0.0000] (n=90255) |
| sibling | B5 Hawiyya (product) | 0.0000 [0.0000, 0.0000] (n=90255) | 0.0472 [0.0458, 0.0486] (n=90255) |
| spouse | B0 identifier exact | 0.1405 [0.1214, 0.1619] (n=1132) | 0.0000 [0.0000, 0.0034] (n=1132) |
| spouse | B4 Hawiyya, forced (no review) | 0.0000 [0.0000, 0.0034] (n=1132) | 0.0000 [0.0000, 0.0034] (n=1132) |
| spouse | B5 Hawiyya (product) | 0.0000 [0.0000, 0.0034] (n=1132) | 0.0027 [0.0009, 0.0078] (n=1132) |
| twin | B0 identifier exact | 0.0148 [0.0118, 0.0186] (n=4867) | 0.0000 [0.0000, 0.0008] (n=4867) |
| twin | B4 Hawiyya, forced (no review) | 0.3392 [0.3261, 0.3526] (n=4867) | 0.0000 [0.0000, 0.0008] (n=4867) |
| twin | B5 Hawiyya (product) | 0.0000 [0.0000, 0.0008] (n=4867) | 0.6396 [0.6260, 0.6530] (n=4867) |

### E7 equity (sealed, product, pooled true pairs, Wilson 95%)

| Stratum | Found recall | LINK recall |
| --- | --- | --- |
| origin gulf_arab | 0.9907 [0.9900, 0.9914] (n=70485) | 0.8311 [0.8283, 0.8339] (n=70485) |
| origin other_arab | 0.9880 [0.9869, 0.9890] (n=42653) | 0.7803 [0.7764, 0.7842] (n=42653) |
| origin south_asian | 0.9925 [0.9918, 0.9932] (n=58886) | 0.7634 [0.7600, 0.7668] (n=58886) |
| origin southeast_asian | 0.9937 [0.9926, 0.9946] (n=23117) | 0.7792 [0.7738, 0.7845] (n=23117) |
| origin western | 0.9951 [0.9939, 0.9961] (n=15669) | 0.7761 [0.7695, 0.7826] (n=15669) |
| scripts ar+ar | 0.9905 [0.9806, 0.9954] (n=740) | 0.8676 [0.8412, 0.8901] (n=740) |
| scripts ar+both | 0.9969 [0.9959, 0.9977] (n=16226) | 0.8938 [0.8889, 0.8984] (n=16226) |
| scripts ar+latin | 0.9903 [0.9894, 0.9911] (n=48581) | 0.7921 [0.7885, 0.7957] (n=48581) |
| scripts both+both | 1.0000 [0.9967, 1.0000] (n=1144) | 0.9344 [0.9186, 0.9474] (n=1144) |
| scripts both+latin | 0.9947 [0.9941, 0.9952] (n=66501) | 0.8343 [0.8315, 0.8371] (n=66501) |
| scripts latin+latin | 0.9878 [0.9870, 0.9885] (n=77618) | 0.7320 [0.7288, 0.7351] (n=77618) |

False merges by origin of the pair: {} (total 0).

### E8 independence: G1 against G2 (sealed)

| System | Found recall G1 | Found recall G2 | Drop | LINK F1 G1 | LINK F1 G2 | False merges per 10k G1 | G2 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| B0 identifier exact | 0.7319 | 0.6884 | 0.0435 | 0.0787 | 0.0719 | 152363.8 | 158460.3 |
| B1 name and date exact | 0.0975 | 0.2023 | -0.1048 | 0.1777 | 0.3365 | 0.5 | 1.1 |
| B2 fuzzy raw names | 0.1572 | 0.1566 | 0.0006 | 0.2716 | 0.2708 | 3.1 | 3.3 |
| B3 Hawiyya, Latin only | 0.9893 | 0.9642 | 0.0251 | 0.8857 | 0.8359 | 0.0 | 0.0 |
| B4 Hawiyya, forced (no review) | 0.9776 | 0.9397 | 0.0380 | 0.9811 | 0.9630 | 137.5 | 107.3 |
| B5 Hawiyya (product) | 0.9913 | 0.9685 | 0.0228 | 0.8840 | 0.8333 | 0.0 | 0.0 |
| B6 supervised reference | 0.9922 | 0.9686 | 0.0236 | 0.9670 | 0.9269 | 0.9 | 0.8 |

Calibration error: G1 0.000454, G2 0.002335.

### E9 review economics (sealed; per 1,000 records; costs in abstract cost units)

Costs: {'c_fm': 500.0, 'c_md': 20.0, 'c_r': 2.0}; simulated reviewer: {'accuracy': 0.97, 'minutes_per_case': 4.0}.

| Quantity | Value |
| --- | --- |
| reviews per 1000 | 231.526 |
| minutes per 1000 | 926.105 |
| residual false merges perfect per 1000 | 0.000 |
| residual missed perfect per 1000 | 7.647 |
| residual false merges reviewer per 1000 | 1.507 |
| residual missed reviewer per 1000 | 12.748 |
| cost hawiyya perfect reviewer | 615.987 |
| cost hawiyya reviewer | 1471.444 |
| cost do nothing | 17876.383 |

| Sweep | Value | Reviews per 1k | False merges per 10k | LINK recall | Found recall |
| --- | --- | --- | --- | --- | --- |
| c_fm | 50 | 156.5 | 0.17 | 0.8740 | 0.9914 |
| c_fm | 100 | 156.5 | 0.17 | 0.8740 | 0.9914 |
| c_fm | 250 | 160.4 | 0.17 | 0.8696 | 0.9914 |
| c_fm | 500 | 231.5 | 0.00 | 0.7901 | 0.9914 |
| c_fm | 1000 | 231.5 | 0.00 | 0.7901 | 0.9914 |
| c_fm | 2000 | 247.1 | 0.00 | 0.7727 | 0.9914 |
| c_fm | 5000 | 247.1 | 0.00 | 0.7727 | 0.9914 |
| c_md | 5 | 189.1 | 0.00 | 0.7901 | 0.9816 |
| c_md | 10 | 214.0 | 0.00 | 0.7901 | 0.9893 |
| c_md | 20 | 231.5 | 0.00 | 0.7901 | 0.9914 |
| c_md | 50 | 255.4 | 0.00 | 0.7901 | 0.9929 |
| c_md | 100 | 267.6 | 0.00 | 0.7901 | 0.9932 |
| c_r | 0.5 | 283.1 | 0.00 | 0.7727 | 0.9932 |
| c_r | 1 | 250.4 | 0.00 | 0.7901 | 0.9926 |
| c_r | 2 | 231.5 | 0.00 | 0.7901 | 0.9914 |
| c_r | 5 | 140.5 | 0.17 | 0.8696 | 0.9888 |
| c_r | 10 | 107.0 | 0.17 | 0.8740 | 0.9782 |
<!-- END:sealed_tables -->
