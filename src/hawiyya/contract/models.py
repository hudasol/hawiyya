"""L0 contract models. The single source of truth for every layer and generated artefact.

Conventions: timestamps are UTC ISO 8601 strings; dates are ISO dates with a precision flag;
probabilities lie in [0, 1]; costs are in abstract cost units.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from hawiyya.contract.enums import (
    AuditKind,
    DatePrecision,
    DecisionKind,
    IdCapture,
    IdKind,
    OriginGroup,
    ReasonCode,
    ReviewState,
    Sex,
)

_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_ISO_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$")

Probability = Field(ge=0.0, le=1.0)


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, use_enum_values=False)


class Record(_Model):
    """Registration view: what a registration form contains, and nothing else."""

    record_id: str = Field(min_length=1, max_length=40)
    facility_id: str = Field(min_length=1, max_length=20)
    name_ar: str | None = Field(
        default=None, max_length=200, description="Name as entered in Arabic script"
    )
    name_latin: str | None = Field(
        default=None,
        max_length=200,
        description="Name as entered in Latin script, possibly Arabizi",
    )
    sex: Sex | None = None
    dob: str | None = Field(default=None, description="Date of birth, ISO date")
    dob_precision: DatePrecision | None = None
    id_value: str | None = Field(default=None, max_length=40)
    id_kind: IdKind | None = None
    id_capture: IdCapture | None = None
    nationality: str | None = Field(default=None, max_length=3, description="ISO 3166 alpha 3 code")
    phone: str | None = Field(default=None, max_length=20)
    area: str | None = Field(default=None, max_length=20, description="Coarse area code")
    registered_on: str = Field(description="Registration date, ISO date")

    @field_validator("dob", "registered_on")
    @classmethod
    def _iso_date(cls, v: str | None) -> str | None:
        if v is not None and not _ISO_DATE.match(v):
            raise ValueError("dates must be ISO YYYY-MM-DD")
        return v

    @model_validator(mode="after")
    def _precision_with_date(self) -> Record:
        if self.dob is not None and self.dob_precision is None:
            raise ValueError("a date of birth needs a precision flag")
        return self


class TruthLabels(_Model):
    """Truth view: generator labels. Never reaches L2 to L5."""

    record_id: str
    person_id: str
    family_id: str
    twin_group: str | None = None
    origin_group: OriginGroup
    facility_style: str
    name_style: str
    corruption_log: list[str] = Field(default_factory=list)


class Comparison(_Model):
    field: str
    level: str


class EvidenceItem(_Model):
    field: str
    level: str
    m: float = Probability
    u: float = Probability
    llr: float = Field(description="Log likelihood ratio, natural log, before frequency adjustment")
    tf_adjustment: float = 0.0
    weight: float = Field(description="llr + tf_adjustment, the contribution to the log odds")
    placeholder: bool = False


class PairScore(_Model):
    record_a: str
    record_b: str
    prior_log_odds: float
    log_odds: float
    probability: float = Probability
    probability_low: float = Probability
    probability_high: float = Probability
    evidence: list[EvidenceItem]
    model_version: str

    @model_validator(mode="after")
    def _interval(self) -> PairScore:
        if not self.probability_low <= self.probability <= self.probability_high:
            raise ValueError("interval must contain the probability")
        return self


class Costs(_Model):
    c_fm: float = Field(gt=0, description="Cost of a false merge")
    c_md: float = Field(gt=0, description="Cost of a missed duplicate")
    c_r: float = Field(gt=0, description="Cost of a review")


class EvidenceObject(_Model):
    pair: PairScore
    complete: bool = Field(description="True when every field comparison was available")
    guards_fired: list[ReasonCode] = Field(default_factory=list)


class Decision(_Model):
    decision: DecisionKind
    model_decision: DecisionKind = Field(description="Decision before guards")
    reason_codes: list[ReasonCode]
    guards_fired: list[ReasonCode]
    evidence: EvidenceObject
    costs: Costs
    expected_costs: dict[str, float]
    thresholds: dict[str, float]
    inputs_hash: str


class Cluster(_Model):
    cluster_id: str
    record_ids: list[str]
    edges: list[tuple[str, str, float]]
    conflict: bool = False
    reason_codes: list[ReasonCode] = Field(default_factory=list)


class ReviewAction(_Model):
    at: str
    actor: str
    from_state: ReviewState
    to_state: ReviewState
    note: str | None = None


class ReviewCase(_Model):
    case_id: str
    record_a: str
    record_b: str
    state: ReviewState
    priority: float
    expected_cost: float
    created_at: str
    decision: Decision
    history: list[ReviewAction] = Field(default_factory=list)


class AuditEvent(_Model):
    seq: int = Field(ge=0)
    at: str
    kind: AuditKind
    subject_ids: list[str]
    inputs_hash: str
    detail: dict[str, Any] = Field(default_factory=dict)
    prev_hash: str
    hash: str

    @field_validator("at")
    @classmethod
    def _utc(cls, v: str) -> str:
        if not _ISO_UTC.match(v):
            raise ValueError("timestamps are stored in UTC, ISO 8601 with Z")
        return v


class Scenario(_Model):
    name: str
    seed: int
    tier: str
    generator: str
    placeholder_share: float | None = None
    costs: Costs | None = None


class ExperimentResult(_Model):
    experiment_id: str
    title: str
    generator: str
    seeds: list[int]
    metrics: dict[str, Any]
    predictions: list[str] = Field(default_factory=list)


ALL_MODELS: list[type[BaseModel]] = [
    Record,
    TruthLabels,
    Comparison,
    EvidenceItem,
    PairScore,
    Costs,
    EvidenceObject,
    Decision,
    Cluster,
    ReviewAction,
    ReviewCase,
    AuditEvent,
    Scenario,
    ExperimentResult,
]

TRUTH_FIELDS = frozenset(TruthLabels.model_fields) - {"record_id"}
