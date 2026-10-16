# ADR 0004: Port, do not import, from Tahdeed

Status: accepted

## Context

Tahdeed (https://github.com/hudasol/tahdeed, MIT, same author) normalises Arabic, English
and Arabizi place names. Hawiyya needs the same ideas for person names. A runtime
dependency would tie Hawiyya to an address project.

## Decision

Pieces are re implemented and re tested in Hawiyya. Source commit for every piece:
`19657f7514037f43fcc6dc9e08c8bc855727678a`.

| Hawiyya module | Tahdeed source | What changed |
| --- | --- | --- |
| `hawiyya.normalise.text` | `src/tahdeed/normalize.py` | Street vocabulary and place stopwords removed; script detection adds Arabizi and "none"; invisible and bidi control characters stripped; article list limited to forms seen in names; Arabic letters written as escapes. Skeleton, coarse key and Arabizi decoding rules kept. |
| `hawiyya.registry.g1.translit` | `src/tahdeed/noise2.py` | Works on person names and the `abd` compound; uses a numpy generator; address parts dropped. Used only by G1. |
| `hawiyya.scoring.calibration` (P4) | idea from `src/tahdeed/calibrate.py` | Isotonic calibration and expected calibration error re implemented for pair probabilities. |
| Evaluation practice (P7, P8) | `docs/PREDICTIONS.md`, `docs/EVALUATION.md` | Sealed split run once, predictions committed first, hits and misses reported. |

Lessons acted on: Arabizi was Tahdeed's weakest style, so it is predicted to be weakest
here; Tahdeed's generator shared assumptions with its matcher, so Hawiyya builds an
independent generator (G2) from the start and enforces its independence with an import
contract.

## Consequences

The README credits Tahdeed with a link and the pinned commit. G2 must not import
`hawiyya.normalise` or `hawiyya.registry.g1`.
