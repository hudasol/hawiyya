# ADR 0003: Synthea CSV schema found

Status: accepted

## Context

The Synthea column layout was not known in advance. It was inspected on the files produced
by the release recorded in `data/MANIFEST.json`.

## Schema found

`patients.csv` header:

```
Id,BIRTHDATE,DEATHDATE,SSN,DRIVERS,PASSPORT,PREFIX,FIRST,MIDDLE,LAST,SUFFIX,MAIDEN,MARITAL,
RACE,ETHNICITY,GENDER,BIRTHPLACE,ADDRESS,CITY,STATE,COUNTY,FIPS,ZIP,LAT,LON,
HEALTHCARE_EXPENSES,HEALTHCARE_COVERAGE,INCOME
```

`encounters.csv` header:

```
Id,START,STOP,PATIENT,ORGANIZATION,PROVIDER,PAYER,ENCOUNTERCLASS,CODE,DESCRIPTION,
BASE_ENCOUNTER_COST,TOTAL_CLAIM_COST,PAYER_COVERAGE,REASONCODE,REASONDESCRIPTION
```

## Decision

The adapter (`hawiyya.registry.source.read_synthea_chunks`) reads only `Id`, `BIRTHDATE`,
`DEATHDATE`, `GENDER` and `COUNTY` from patients and `PATIENT` from encounters. It keeps
living patients, maps each county to an opaque region code (`R01` and so on) and counts
encounters. Names, identifiers, addresses, race, ethnicity and income are never read.

The adapter fails loudly with `SchemaDriftError`, naming the file and the column, when a
required column is missing, a birth date is not ISO, or a sex code is not `M` or `F`. A test
covers each case.
