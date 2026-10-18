# ADR 0009: Static and live modes, mixed script rendering

Status: accepted

## Static and live modes

- **Live mode:** `hawiyya serve` starts the FastAPI service on the demonstration registry
  (development seed 7, Tier S). The console in development (`npm run dev`) proxies `/v1` to
  it. The first request builds the registry (about ten seconds).
- **Static mode:** `hawiyya snapshot` writes every response the console needs to
  `web/public/snapshot/`; `npm run build:static` builds a site that needs no backend and can
  be hosted on any free static host. The registration check and the name lab then offer
  precomputed examples and say so on screen. A browser side scorer is a SHOULD item (P9).
- The console uses hash routing so a static host needs no rewrite rules.

## Mixed script rendering

Every person name and identifier is rendered by `Name` or `Ident`, which wrap the value in
a `<bdi>` element (`dir="auto"` for names, `dir="ltr"` for identifiers and dates), so Arabic
and Latin text never reorder the digits and punctuation around them. A component test and an
end to end test check that every element marked as a name is a `bdi`. Layout uses CSS
logical properties so the right to left mirror needs no separate stylesheet. Charts mirror
their axis in right to left so evidence for a match grows towards the end side.

## Consequences

The static demo cannot score arbitrary input. Tests run the live API on a smaller registry
(tier XS) through an environment variable so the fast check stays fast.
