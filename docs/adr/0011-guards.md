# ADR 0011: Guards on top of the model

Status: accepted

Guards encode safety knowledge that a conditionally independent model cannot learn. Each
guard has a reason code, can only turn a model LINK into REVIEW, and is evaluated only when
the model would LINK (so the reported guards are those that changed the outcome).

| Guard | Rule |
| --- | --- |
| HARD_CONFLICT | The identifier level is "different (card reader)": two different card read identifiers of the same kind. |
| POSSIBLE_TWIN_OR_SIBLING | Date of birth equal or close (exact, transposed, one digit, year off), family name agrees, father's name agrees or is missing, the identifiers do not agree, and the given names are different names in every rendering pair. Different names means different skeletons, or Latin spellings at least three edits apart (Hasan and Hussain), so spelling variants (Ahmed and Ahmad) do not trigger it. |
| POSSIBLE_PARENT_CHILD_SHARED_ID | The identifier level is "shared substitute": a declared newborn substitute or an age gap of 12 years or more. |
| PLACEHOLDER_ONLY | Both records carry the same placeholder identifier and the dates of birth do not agree exactly. |
| COMMON_NAME_ONLY | All positive evidence comes from name fields; date of birth, identifier and phone contribute nothing positive. |
| DOB_PLACEHOLDER_SUSPECTED | The date of birth level is placeholder (pattern or learned default) and the identifiers do not agree. |

Each guard has a test that triggers it and a test that it does not over trigger on a close
but legitimate pair. A known cost: the twin guard can fire on true duplicates whose Arabizi
spelling changes the skeleton of the given name; this errs towards review and is measured in
the evaluation.
