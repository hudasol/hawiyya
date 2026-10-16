# Data statement

All patients in this repository are synthetic. Identifiers are synthetic and belong to no
person. Results describe synthetic data and say nothing about any real registry.

## Source

<!-- BEGIN:data_source -->
Data source: Synthea

- Synthea release tag `master-branch-latest`, jar SHA 256 `018ad7f04f7aacb995804d7d4781c76d5fc714f7f23257ba50daa9eefae224ac`.
- 10 deterministic runs, reference date 2026-01-01, 25000 living synthetic patients kept.
- Kept columns: `person_id`, `birth_date`, `sex`, `region`, `encounters`.
- Name lexicon author: `build_agent`.
- Exact commands and file hashes: `data/MANIFEST.json`.
<!-- END:data_source -->

Synthea models a population in the United States. Its age and sex structure is not the
UAE's, and no claim is made that it is. An optional re weighting by sex
(`hawiyya.registry.source.reweight`, labelled ASSUMPTION) exists for experiments; the
default build does not use it. If Java or Synthea were unavailable, the native generator
(`hawiyya.registry.source.native_population`) produces the same schema with an age pyramid
chosen by the author (ASSUMPTION), and every label is switched by the manifest.

## What is generated, and by what

| Part | Produced by | Status |
| --- | --- | --- |
| Birth date, sex, coarse region, encounter count | the population source above | synthetic |
| Households, clans, twins, same name fathers and sons, newborns | `hawiyya.registry.people` | synthetic, rates are ASSUMPTION |
| Names (as lexicon entries) | `data/lexicon/names.json`, author `build_agent` | written by the build agent, not drawn from any register |
| Identifiers, passports, Gulf identity numbers, phones, areas | `hawiyya.registry.people` | random, synthetic |
| Registrations at six synthetic facilities and their errors | G1 (`hawiyya.registry.g1`) | rates are ASSUMPTION, no claim of realism |
| Independent registrations | G2 (`hawiyya.registry.g2`) | see P7 |

## Identifiers

The national identity style numbers are 15 digits: the prefix 784, the person's birth year
and eight random digits. This layout follows a public description of the format (see
`docs/CONTEXT.md`, Source B). No check digit is computed because no source for its rule was
opened. The values are generated at random, are not drawn from any registry, and could
coincide with a real number only by chance; they carry no information about any person.
Passport, Gulf identity, file and phone numbers are generated the same way.

Placeholder identifiers: "All 1" (fifteen ones) follows the public policy reading in
`docs/CONTEXT.md` (Source A, sections 4.6.6 and 4.6.7). The other placeholder values
(all zeros, all nines, 784 followed by zeros, an ascending sequence) are ASSUMPTION.
Newborns under three months are registered under the mother's identifier, following the
same reading (Source A, section 4.6.4).

## Names

The lexicon holds given names by sex and origin group and family or tribal names, each with
an Arabic form and Latin variants. Ruling family names are excluded and a denylist refuses
given and family combinations that form the name of a well known public figure
(`data/lexicon/denylist.json`, enforced by a test). Arabic forms of names that are not of
Arabic origin are the author's transliterations and need review by a native speaker.

Name origin groups (Gulf Arab, other Arab, South Asian, Southeast Asian, Western) are coarse
generator labels. They are used only to stratify results and never reach the matcher.

## Limitations

The data are synthetic and so are the errors. Rates of placeholders, typing errors and
script choices are the author's assumptions. Nothing here describes any real registry.
