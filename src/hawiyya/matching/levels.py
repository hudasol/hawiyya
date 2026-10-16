"""Comparison fields and their discrete levels.

Each field has an ordered list of levels. Order runs from strongest agreement to strongest
disagreement, with "missing" and placeholder levels carrying no evidence. Every level has a
name that the evidence table shows, in English and Arabic.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FieldSpec:
    name: str
    levels: tuple[str, ...]
    neutral: frozenset[str]  # levels that carry no evidence by construction (weight 0)
    label_en: str
    label_ar: str

    def index(self, level: str) -> int:
        return self.levels.index(level)


NAME_LEVELS = ("exact", "skeleton", "coarse", "edit1", "initial", "missing", "mismatch")

FIELDS: tuple[FieldSpec, ...] = (
    FieldSpec("given", NAME_LEVELS, frozenset({"missing"}), "Given name", "الاسم الأول"),
    FieldSpec("family", NAME_LEVELS, frozenset({"missing"}), "Family name", "اسم العائلة"),
    FieldSpec("father", NAME_LEVELS, frozenset({"missing"}), "Father's name", "اسم الأب"),
    FieldSpec("whole_name", ("very_close", "close", "far", "not_comparable"),
              frozenset({"not_comparable"}), "Whole name spelling", "تهجئة الاسم كاملا"),
    FieldSpec("dob", ("exact", "transposed", "digit1", "year_off", "year_only", "missing",
                      "placeholder", "conflict"),
              frozenset({"missing", "placeholder"}), "Date of birth", "تاريخ الميلاد"),
    FieldSpec("sex", ("agree", "missing", "disagree"), frozenset({"missing"}), "Sex", "الجنس"),
    FieldSpec("identifier", ("exact", "edit1", "shared_substitute", "missing", "placeholder",
                             "different_kinds", "different_manual", "different_reader"),
              frozenset({"missing", "placeholder"}), "Identifier", "رقم الهوية"),
    FieldSpec("phone", ("exact", "missing", "different"), frozenset({"missing"}), "Phone",
              "الهاتف"),
    FieldSpec("nationality", ("agree", "missing", "different"), frozenset({"missing"}),
              "Nationality", "الجنسية"),
    FieldSpec("area", ("agree", "missing", "different"), frozenset({"missing"}), "Area",
              "المنطقة"),
)  # fmt: skip

FIELD_INDEX = {f.name: i for i, f in enumerate(FIELDS)}

# Sign constraints used by L4: a disagreement is never evidence for a match, and full agreement
# is never evidence against one.
DISAGREEMENT_LEVELS = frozenset({"mismatch", "conflict", "disagree", "different", "far",
                                 "different_kinds", "different_manual", "different_reader"})  # fmt: skip
AGREEMENT_LEVELS = frozenset({"exact", "agree", "very_close"})
N_FIELDS = len(FIELDS)


def spec(name: str) -> FieldSpec:
    return FIELDS[FIELD_INDEX[name]]


LEVEL_LABELS: dict[str, dict[str, str]] = {
    "exact": {"en": "same", "ar": "متطابق"},
    "skeleton": {"en": "same consonants", "ar": "الحروف الساكنة نفسها"},
    "coarse": {"en": "similar consonants", "ar": "حروف ساكنة متشابهة"},
    "edit1": {"en": "one character apart", "ar": "يختلف بحرف واحد"},
    "initial": {"en": "initial or abbreviation", "ar": "حرف أول أو اختصار"},
    "missing": {"en": "missing on one side", "ar": "غير موجود في أحد السجلين"},
    "mismatch": {"en": "different", "ar": "مختلف"},
    "very_close": {"en": "very close spelling", "ar": "تهجئة متقاربة جدا"},
    "close": {"en": "close spelling", "ar": "تهجئة متقاربة"},
    "far": {"en": "different spelling", "ar": "تهجئة مختلفة"},
    "not_comparable": {"en": "not comparable", "ar": "غير قابل للمقارنة"},
    "transposed": {"en": "day and month swapped", "ar": "اليوم والشهر مقلوبان"},
    "digit1": {"en": "one digit apart", "ar": "يختلف برقم واحد"},
    "year_off": {"en": "year off by one", "ar": "السنة مختلفة بسنة واحدة"},
    "year_only": {"en": "same year only", "ar": "السنة فقط متطابقة"},
    "placeholder": {"en": "placeholder value, no evidence", "ar": "قيمة مؤقتة لا تعد دليلا"},
    "conflict": {"en": "different", "ar": "مختلف"},
    "agree": {"en": "same", "ar": "متطابق"},
    "disagree": {"en": "different", "ar": "مختلف"},
    "shared_substitute": {"en": "shared substitute identifier", "ar": "رقم بديل مشترك"},
    "different_kinds": {"en": "different identifier kinds", "ar": "أنواع هوية مختلفة"},
    "different_manual": {"en": "different (typed by hand)", "ar": "مختلف (إدخال يدوي)"},
    "different_reader": {"en": "different (card reader)", "ar": "مختلف (قارئ البطاقة)"},
    "different": {"en": "different", "ar": "مختلف"},
}
