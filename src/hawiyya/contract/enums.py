"""L0 enumerations: identifier kinds, capture methods, decisions, reason codes, states.

Arabic descriptions are machine drafted by the author and need review by a native speaker.
"""

from __future__ import annotations

from enum import StrEnum


class IdKind(StrEnum):
    EID = "EID"
    PASSPORT = "PASSPORT"
    GCC_ID = "GCC_ID"
    FILE_NO = "FILE_NO"
    MOTHER_EID = "MOTHER_EID"
    PLACEHOLDER = "PLACEHOLDER"


class IdCapture(StrEnum):
    READER = "reader"
    MANUAL = "manual"
    SUBSTITUTE = "substitute"
    PLACEHOLDER = "placeholder"


class Sex(StrEnum):
    MALE = "M"
    FEMALE = "F"
    UNKNOWN = "U"


class DatePrecision(StrEnum):
    DAY = "day"
    MONTH = "month"
    YEAR = "year"


class DecisionKind(StrEnum):
    LINK = "LINK"
    REVIEW = "REVIEW"
    KEEP_APART = "KEEP_APART"


class ReasonCode(StrEnum):
    STRONG_ID_AGREEMENT = "STRONG_ID_AGREEMENT"
    STRONG_DEMOGRAPHIC_AGREEMENT = "STRONG_DEMOGRAPHIC_AGREEMENT"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    PLACEHOLDER_ONLY = "PLACEHOLDER_ONLY"
    COMMON_NAME_ONLY = "COMMON_NAME_ONLY"
    POSSIBLE_TWIN_OR_SIBLING = "POSSIBLE_TWIN_OR_SIBLING"
    POSSIBLE_PARENT_CHILD_SHARED_ID = "POSSIBLE_PARENT_CHILD_SHARED_ID"
    DOB_PLACEHOLDER_SUSPECTED = "DOB_PLACEHOLDER_SUSPECTED"
    CLUSTER_CONFLICT = "CLUSTER_CONFLICT"
    HARD_CONFLICT = "HARD_CONFLICT"


REASON_TEXT: dict[ReasonCode, dict[str, str]] = {
    ReasonCode.STRONG_ID_AGREEMENT: {
        "en": "The two records share the same valid identifier.",
        "ar": "يشترك السجلان في رقم تعريف صالح واحد.",
    },
    ReasonCode.STRONG_DEMOGRAPHIC_AGREEMENT: {
        "en": "Names, date of birth and other details agree strongly.",
        "ar": "تتطابق الأسماء وتاريخ الميلاد والتفاصيل الأخرى بدرجة عالية.",
    },
    ReasonCode.INSUFFICIENT_EVIDENCE: {
        "en": "There is not enough evidence to decide automatically.",
        "ar": "لا توجد أدلة كافية لاتخاذ قرار تلقائي.",
    },
    ReasonCode.CONFLICTING_EVIDENCE: {
        "en": "Some details agree and others disagree.",
        "ar": "بعض التفاصيل متطابقة وبعضها مختلف.",
    },
    ReasonCode.PLACEHOLDER_ONLY: {
        "en": "The only shared identifier is a placeholder, which proves nothing.",
        "ar": "الرقم المشترك الوحيد رقم مؤقت لا يثبت شيئا.",
    },
    ReasonCode.COMMON_NAME_ONLY: {
        "en": "The records agree mainly on common names.",
        "ar": "يتفق السجلان أساسا في أسماء شائعة.",
    },
    ReasonCode.POSSIBLE_TWIN_OR_SIBLING: {
        "en": "The records may belong to twins or siblings.",
        "ar": "قد يعود السجلان إلى توأمين أو شقيقين.",
    },
    ReasonCode.POSSIBLE_PARENT_CHILD_SHARED_ID: {
        "en": "A parent and a child may share one identifier.",
        "ar": "قد يشترك أحد الوالدين وطفل في رقم تعريف واحد.",
    },
    ReasonCode.DOB_PLACEHOLDER_SUSPECTED: {
        "en": "The date of birth looks like a default value.",
        "ar": "يبدو تاريخ الميلاد قيمة افتراضية.",
    },
    ReasonCode.CLUSTER_CONFLICT: {
        "en": "Linking would join records that contradict each other.",
        "ar": "الربط سيجمع سجلات متعارضة فيما بينها.",
    },
    ReasonCode.HARD_CONFLICT: {
        "en": "Two different card read identifiers of the same kind disagree.",
        "ar": "رقمان مختلفان من النوع نفسه قرئا من البطاقة.",
    },
}


class ReviewState(StrEnum):
    OPEN = "OPEN"
    ASSIGNED = "ASSIGNED"
    CONFIRMED_MERGE_REQUEST = "CONFIRMED_MERGE_REQUEST"
    KEPT_APART = "KEPT_APART"
    CROSS_REFERENCED = "CROSS_REFERENCED"
    NEEDS_INFORMATION = "NEEDS_INFORMATION"


class OriginGroup(StrEnum):
    """Generator label used only to stratify results. Never a model input."""

    GULF_ARAB = "gulf_arab"
    OTHER_ARAB = "other_arab"
    SOUTH_ASIAN = "south_asian"
    SOUTHEAST_ASIAN = "southeast_asian"
    WESTERN = "western"


class AuditKind(StrEnum):
    SCORE = "score"
    DECISION = "decision"
    REVIEW_ACTION = "review_action"
    EXPORT = "export"
    CHECK = "check"
