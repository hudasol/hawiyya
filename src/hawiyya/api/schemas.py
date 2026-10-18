"""Request and response models for the HTTP API. Every input is bounded."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from hawiyya.contract.enums import DatePrecision, IdCapture, IdKind, Sex
from hawiyya.contract.models import PairScore

SYNTHETIC_NOTE = (
    "All patients in this demonstration are synthetic. Identifiers are synthetic and belong to "
    "no person. Results describe synthetic data and say nothing about any real registry."
)


class _In(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RegistrationInput(_In):
    """A registration form, without the record id and date (assigned by the service)."""

    name_ar: str | None = Field(default=None, max_length=120)
    name_latin: str | None = Field(default=None, max_length=120)
    sex: Sex | None = None
    dob: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    dob_precision: DatePrecision | None = None
    id_value: str | None = Field(default=None, max_length=30)
    id_kind: IdKind | None = None
    id_capture: IdCapture | None = None
    nationality: str | None = Field(default=None, max_length=3)
    phone: str | None = Field(default=None, max_length=20)
    area: str | None = Field(default=None, max_length=10)
    top: int = Field(default=10, ge=1, le=25)


class ScoreInput(_In):
    a: RegistrationInput
    b: RegistrationInput


class ActionInput(_In):
    action: Literal["assign", "request_merge", "keep_apart", "cross_reference",
                    "need_information", "reopen"]  # fmt: skip


class NameInput(_In):
    name: str = Field(min_length=1, max_length=120)
    other: str | None = Field(default=None, max_length=120)


ADVISORY_NOTE = (
    "Advisory software for planning and learning. Recommendations are requests to a human "
    "reviewer, never automatic actions."
)


class Envelope(BaseModel):
    synthetic_note: str = SYNTHETIC_NOTE
    advisory_note: str = ADVISORY_NOTE
    mode: str = "live"


class CandidateOut(BaseModel):
    record: dict[str, Any]
    score: PairScore
    decision: dict[str, Any] | None = None


class CheckOut(Envelope):
    ok: bool
    n_scored: int
    candidates: list[CandidateOut]
    note: str = ""
    next_best_question: list[dict[str, Any]] | None = None
