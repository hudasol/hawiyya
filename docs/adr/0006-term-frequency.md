# ADR 0006: Term frequency adjustment

Status: accepted

## Context

Agreement on a rare name is stronger evidence than agreement on a common one (two records
that both say Mohammed tell us little). The same holds for a common date of birth and a
shared household phone.

## Decision

- Frequencies are counted from the registry itself (`hawiyya.normalise.record.build_tf`),
  never from the generator or its lexicon: given and family name skeleton keys, day precise
  dates of birth and phone numbers.
- For a pair that agrees (exact or skeleton level for names, exact for dates and phones) the
  adjustment is `ln(tf_bar / tf_value)`, where `tf_bar` is the frequency weighted mean
  frequency (`sum tf^3 / sum tf^2`) of that table. A value as frequent as the typical agreeing
  value gets no adjustment; rarer values gain, commoner values lose.
- Each adjustment is clipped to plus or minus 2 (ASSUMPTION) and floored so that an agreeing
  level with a positive weight never ends below zero.
- When a record holds several renderings, the most frequent shared key is used (the
  conservative choice).
- Placeholder and missing levels are never adjusted.

## Consequences

The evidence table shows the base weight and the adjustment separately, so a reviewer sees
when a common name was discounted. Frequencies count records rather than people, so a person
registered four times inflates their own name's frequency slightly.
