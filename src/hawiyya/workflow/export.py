"""Exports: a FHIR R4 style Patient bundle with Patient.link, a CSV of review cases and a one
page summary. Each carries the statement below. Structure only; no conformance claim.

Link semantics for a merge request: the surviving record ``replaces`` the others and each
other record is ``replaced-by`` the survivor (marked inactive). For a cross reference both
records point at each other with ``seealso``.
"""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Sequence
from typing import Any

import jsonschema

from hawiyya.contract.enums import IdCapture, IdKind
from hawiyya.contract.models import Record, ReviewCase
from hawiyya.core.paths import CONTRACT_DIR

STATEMENT = ("Synthetic data, for review only, structure only, no conformance claim. "
             "Advisory output for planning and learning; not a record of any real person.")  # fmt: skip
SYNTHETIC_TAG = {"system": "urn:hawiyya:tags", "code": "synthetic", "display": STATEMENT}
SCHEMA_PATH = CONTRACT_DIR / "fhir_patient_bundle.schema.json"
GENDER = {"M": "male", "F": "female", "U": "unknown"}


def survivor(records: Sequence[Record]) -> Record:
    """Prefer a card read identifier, then the earliest registration, then the lowest id."""
    def key(r: Record) -> tuple[int, str, str]:
        return (0 if r.id_capture == IdCapture.READER else 1, r.registered_on, r.record_id)

    return sorted(records, key=key)[0]


def _patient(r: Record) -> dict[str, Any]:
    res: dict[str, Any] = {"resourceType": "Patient", "id": r.record_id,
                           "meta": {"tag": [SYNTHETIC_TAG]}, "active": True}  # fmt: skip
    if r.id_value and r.id_kind and r.id_kind != IdKind.PLACEHOLDER:
        res["identifier"] = [{"system": f"urn:hawiyya:synthetic:{r.id_kind.value.lower()}",
                              "value": r.id_value}]  # fmt: skip
    names = [{"text": n} for n in (r.name_latin, r.name_ar) if n]
    if names:
        res["name"] = names
    if r.sex:
        res["gender"] = GENDER[r.sex.value]
    if r.dob:
        res["birthDate"] = r.dob
    return res


def fhir_bundle(records: Sequence[Record], cross_reference: bool = False) -> dict[str, Any]:
    """Bundle for one cluster (merge request) or one cross referenced pair."""
    pats = {r.record_id: _patient(r) for r in records}
    if cross_reference:
        ids = sorted(pats)
        for rid in ids:
            pats[rid]["link"] = [{"other": {"reference": f"Patient/{o}"}, "type": "seealso"}
                                 for o in ids if o != rid]  # fmt: skip
    else:
        keep = survivor(records).record_id
        pats[keep]["link"] = [{"other": {"reference": f"Patient/{o}"}, "type": "replaces"}
                              for o in sorted(pats) if o != keep]  # fmt: skip
        for rid in sorted(pats):
            if rid != keep:
                pats[rid]["active"] = False
                pats[rid]["link"] = [{"other": {"reference": f"Patient/{keep}"},
                                      "type": "replaced-by"}]  # fmt: skip
    return {
        "resourceType": "Bundle", "type": "collection",
        "meta": {"tag": [SYNTHETIC_TAG]},
        "extension": [{"url": "urn:hawiyya:statement", "valueString": STATEMENT}],
        "entry": [{"resource": pats[k]} for k in sorted(pats)],
    }  # fmt: skip


def validate_bundle(bundle: dict[str, Any]) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(bundle, schema)


CSV_COLUMNS = ("case_id", "record_a", "record_b", "state", "priority", "probability",
               "decision", "reason_codes")  # fmt: skip


def review_csv(cases: Sequence[ReviewCase]) -> str:
    buf = io.StringIO(newline="")
    buf.write("# " + STATEMENT + "\n")
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(CSV_COLUMNS)
    for c in cases:
        w.writerow([c.case_id, c.record_a, c.record_b, c.state.value, c.priority,
                    round(c.decision.evidence.pair.probability, 6), c.decision.decision.value,
                    " ".join(r.value for r in c.decision.reason_codes)])  # fmt: skip
    return buf.getvalue()


def one_page_summary(stats: dict[str, Any]) -> str:
    lines = ["# Hawiyya review summary (synthetic)", "", STATEMENT, ""]
    for k in sorted(stats):
        lines.append(f"- {k.replace('_', ' ')}: {stats[k]}")
    lines.append("")
    return "\n".join(lines)
