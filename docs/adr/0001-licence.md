# ADR 0001: Licence

Status: accepted

## Context

Hawiyya is an open source proposal seed. It ports small pieces of ideas and code from
Tahdeed (MIT licence, by the same author) and may use Synthea (Apache License 2.0) at
build time to generate synthetic populations.

## Decision

Hawiyya is released under the Apache License 2.0 (`LICENSE`).

- Apache 2.0 is compatible with porting MIT licensed code. Each ported piece is recorded in
  ADR 0004 with the source file and pinned commit, and the README keeps the attribution.
- The Synthea jar is never committed. Any committed sample derived from Synthea output
  carries `data/NOTICE.md`.
- The explicit patent grant of Apache 2.0 suits a project that a public body might later
  study or adapt.

## Consequences

Contributors must keep the attribution for ported pieces and the data notice. No
dependency with a licence incompatible with Apache 2.0 may be added.
