# ADR 0010: Cost based decision

Status: accepted

## Decision

With calibrated probability p, Hawiyya chooses the action with the lowest expected cost:
LINK costs C_FM (1 - p), KEEP_APART costs C_MD p, REVIEW costs C_R. In closed form:

- t_link = 1 - C_R / C_FM: LINK when p > t_link.
- t_keep = C_R / C_MD: KEEP_APART when p < t_keep.
- REVIEW in between. When t_keep >= t_link the review band vanishes and the choice is LINK
  when p > t_mid = C_FM / (C_FM + C_MD).
- On a boundary the less permissive action wins.

Defaults (ASSUMPTION, swept in E9): C_FM = 500, C_MD = 20, C_R = 2, giving t_link = 0.996
and t_keep = 0.1. A false merge is the most expensive error because it can lead to the wrong
patient's record being used; a missed duplicate is milder; a review is cheap but not free.

LINK means "recommend a merge request to the health information management office". It is
never an automatic merge.

## Properties tested (hypothesis)

A higher probability never gives a less permissive decision; raising C_FM never adds a LINK;
raising C_R never adds a REVIEW; the chosen action always has the minimum expected cost.

## Fail closed

No LINK is returned unless the evidence object is complete (one item per field, items adding
up to the log odds). Registration itself fails open: an error in the check returns an empty
advisory result.
