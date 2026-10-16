# Context: public sources

This is the only file in the repository that names real organisations. They appear only as
the publishers of public documents. Every page below was opened during the build in
October 2026 and the items listed were checked against the extracted text. The reading is
the author's.

Hawiyya does not model any real registry. No entity requested, reviewed or endorses this
work. Hawiyya makes no claim about the compliance of any entity with any policy.

## Source A: health data quality policy (primary)

<a id="source-a"></a>
Dubai Health Authority, *Policy for Health Data Quality*, reference DHA/HISHD/PP-08,
issue 02, issue date 1 August 2023, effective date 1 November 2023.
https://www.dha.gov.ae/uploads/082022/Health%20Data%20Quality%20Policy2022839141.pdf

What the policy says, in brief paraphrase (section numbers as printed):

<a id="source-a-4-5-6"></a>
- Section 4.5.6: where several referrals or episodes exist, interventions must be linked
  correctly through the patient unique identifier.

<a id="source-a-4-5-8"></a>
- Section 4.5.8: patients must not have duplicated records. When a duplicate is detected,
  a call is raised to the entity's health information management department to request a
  merge; if the records cannot be merged for legal or technical reasons, they must be cross
  referenced.

<a id="source-a-4-6-3"></a>
- Section 4.6.3: entities must use an identity card reader when registering a patient.

<a id="source-a-4-6-4"></a>
- Section 4.6.4: when the national identity number is not available, substitutes apply:
  tourists and new visitors use a file number or a UID number; newborns under three months
  use the mother's identity number (or file number if the mother is a tourist); nationals of
  Gulf Cooperation Council countries use their country identity number; diplomats use a
  passport number.

<a id="source-a-4-6-6"></a>
- Sections 4.6.6 and 4.6.7: a patient with no identity card and no passport may be
  registered with the identity number entered as "All 1", in an emergency, and otherwise
  while keeping a record of an official identity such as the date of birth.

<a id="source-a-4-6-8"></a>
- Section 4.6.8: the identity number or its substitute is a mandatory field and the unique
  patient identifier.

<a id="source-a-4-8"></a>
- Sections 4.8.1 and 4.8.2: completeness and error thresholds. For example, any single error
  in the identity number or the passport name counts as a breach, and an error rate of at
  least 1 percent in one week in nationality, date of birth, gender or telephone number
  counts as a breach.

<a id="source-a-4-9-8"></a>
- Section 4.9.8: entities should perform regular (for example weekly) data quality audits,
  including a check for duplicate records.

<a id="source-a-gap"></a>
**The gap Hawiyya addresses (the author's reading).** The policy requires that duplicates
be found and merged or cross referenced, and allows "All 1" as a placeholder identifier.
It does not define matching rules, a duplicate detection method, or how records registered
with "All 1" are later corrected. A search of the extracted text for matching or algorithm
terms found none. Hawiyya proposes one way to fill that gap and is not part of the policy.

## Source B: another emirate's regulator (secondary)

<a id="source-b"></a>
Department of Health Abu Dhabi, *Standard 1: Patient Identifier (Emirates ID and
Passport)*, a one page standard.
https://www.doh.gov.ae/-/media/Feature/Resources/Health-Information-Exchange-standards/Standard-1---Patient-Identifier---Emirates-ID-and-Passport.ashx

<a id="source-b-matching"></a>
- It states that poor capture of demographic information affects patient matching in the
  emirate's health information exchange and increases the likelihood of duplicate patient
  records.

<a id="source-b-format"></a>
- It describes the identity number as a 15 digit continuous string and gives an example
  that begins with 784 followed by a four digit year. Hawiyya's synthetic identifier format
  follows this description; no check digit rule is given there, so none is computed.

This standard is cited only as another emirate's regulator. Its wording is not attributed to
Source A's publisher.

## Source C: identity management policy (read, not cited for duplicates)

<a id="source-c"></a>
Dubai Health Authority, *NABIDH Policies and Standards: Identity Management Policy*,
last updated 1 September 2020.
https://www.dha.gov.ae/uploads/102022/NABIDH%20Policies%20&%20Standards%20-%20Identity%20Management%20Policy2022104825.pdf

<a id="source-c-primary-id"></a>
- Section 3.2.6 (b and c): for identity proofing, the national identity card is the primary
  identification document, with a passport or other government documents accepted in its
  absence.

This document is about proving identity for access to an information exchange. It does not
discuss duplicate records, merging or placeholder identifiers, and Hawiyya does not cite it
for those topics.

## Source D: Synthea

<a id="source-d"></a>
Synthea, synthetic patient population simulator. https://github.com/synthetichealth/synthea

<a id="source-d-facts"></a>
- Licensed under the Apache License 2.0; requires Java JDK 17 or newer; the CSV exporter is
  enabled with `exporter.csv.export = true`; the command line takes a seed (`-s`), a
  clinician seed (`-cs`), a reference date (`-r`, YYYYMMDD) and a population size (`-p`).

Synthea's demographics model a population in the United States and are not those of the
UAE. Hawiyya keeps only birth date, sex, a coarse region and an encounter count from it.

## Source E: Tahdeed

<a id="source-e"></a>
Tahdeed, by the same author (MIT licence), pinned to commit
19657f7514037f43fcc6dc9e08c8bc855727678a. https://github.com/hudasol/tahdeed

Hawiyya ports its Arabic and Arabizi normalisation ideas and small pieces of code (see
`docs/adr/0004-port-from-tahdeed.md`).
