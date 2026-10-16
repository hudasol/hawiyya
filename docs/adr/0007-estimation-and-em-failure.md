# ADR 0007: Parameter estimation, the EM failure mode and sign constraints

Status: accepted

## Context

The brief asks for unsupervised EM with informed initialisation, a label fitted upper bound,
and an honest report of the gap. Fit diagnostics are in `results/model/fit_report.json`
(development seeds 1 to 3 for fitting, 4 and 5 for checking).

## What happened

Plain EM (m and u free, u initialised from random pairs, m initialised from the level order)
converged in 20 iterations to lambda 0.161 while the true match share among candidate pairs
was 0.083. Conditional independence is false: siblings and spouses share family names,
fathers, phones and areas, and EM's "match" class absorbed households. Its average precision
on the check seeds was 0.9598 against 0.9992 for the label fit. EM with u held at the random
pair estimate diverged to lambda near 1, because random pairs agree far less than blocked
candidates do.

## Decision

The product uses **anchored estimation**, which uses no ground truth labels:

- m for every field except the identifier comes from pairs whose non placeholder,
  non substitute identifiers agree exactly; m for the identifier comes from pairs whose given
  and family names agree and whose dates of birth agree exactly.
- u for every field except the identifier comes from pairs whose identifiers are different
  values of the same kind (a sample of candidate non matches that includes siblings and other
  hard negatives); u for the identifier comes from pairs whose dates of birth conflict and
  given names differ.
- lambda is estimated by EM with m and u fixed.

On the check seeds anchored estimation reached lambda 0.0849 (true 0.0832) and average
precision 0.9991. Plain EM is kept in the model file and the report for comparison.

**Sign constraints.** Estimated on blocked candidate pairs, a family name mismatch came out
as positive evidence (blocking gathers same family non matches, so mismatches are rare among
candidate non matches). Weights of disagreement levels are therefore capped at zero and
weights of full agreement levels floored at zero. Raw m and u are still reported.

## Consequences

Anchored estimation depends on exact identifier agreement being common and mostly correct.
Where identifiers are rare or unreliable (for example a registry dominated by placeholders),
anchors thin out; E5 and E8 test this. The anchors are deterministic rules, which is a known
practice in record linkage, but they share an assumption with the generator (that a real,
equal identifier means the same person), which the independent generator G2 also makes.
