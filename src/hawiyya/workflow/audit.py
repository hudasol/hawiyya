"""Append only audit log with a hash chain.

Every score, decision, review action and export is recorded with the inputs hash, a UTC
timestamp, the previous event's hash and its own hash. Editing, removing or reordering any line
breaks the chain, which ``verify`` detects. Names and identifiers are never written: subjects
are record or case ids, and detail values must pass the safe logging check.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from hawiyya.contract.enums import AuditKind
from hawiyya.contract.models import AuditEvent
from hawiyya.core.determinism import canonical_json
from hawiyya.core.safelog import is_hash, is_safe_value

GENESIS = "0" * 64


def _digest(body: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(body).encode("utf-8")).hexdigest()


class AuditLog:
    """In memory chain, optionally mirrored to a JSON lines file."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path
        self.events: list[AuditEvent] = []
        if path is not None and path.exists():
            self.events = [AuditEvent.model_validate_json(line)
                           for line in path.read_text(encoding="utf-8").splitlines() if line]  # fmt: skip

    @property
    def head(self) -> str:
        return self.events[-1].hash if self.events else GENESIS

    def append(self, kind: AuditKind, subject_ids: Iterable[str], inputs_hash: str, at: str,
               detail: dict[str, Any] | None = None) -> AuditEvent:
        detail = detail or {}
        subjects = list(subject_ids)
        if not is_hash(inputs_hash):
            raise ValueError("inputs_hash must be a hexadecimal digest")
        for v in (*subjects, *detail.values()):
            if not is_safe_value(v):
                raise ValueError("audit values must be ids, hashes, counts or fixed labels")
        body = {"seq": len(self.events), "at": at, "kind": kind.value, "subject_ids": subjects,
                "inputs_hash": inputs_hash, "detail": detail, "prev_hash": self.head}  # fmt: skip
        ev = AuditEvent.model_validate({**body, "hash": _digest(body)})
        self.events.append(ev)
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8", newline="\n") as fh:
                fh.write(ev.model_dump_json() + "\n")
        return ev


def verify(events: list[AuditEvent]) -> int | None:
    """Return the sequence number of the first broken event, or None when the chain holds."""
    prev = GENESIS
    for i, ev in enumerate(events):
        body = ev.model_dump(mode="json", exclude={"hash"})
        if ev.seq != i or ev.prev_hash != prev or _digest(body) != ev.hash:
            return i
        prev = ev.hash
    return None


def verify_file(path: Path) -> int | None:
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line]
    events = []
    for i, line in enumerate(lines):
        try:
            events.append(AuditEvent.model_validate(json.loads(line)))
        except (ValueError, json.JSONDecodeError):
            return i
    return verify(events)
