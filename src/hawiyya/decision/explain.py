"""Three sentence explanations rendered from the evidence object, in English and Arabic.

Sentence 1: what to do. Sentence 2: why (the strongest evidence and any guard). Sentence 3:
what would change it. The text is rendered from the Decision and is never the source of truth.
Arabic copy is machine drafted and needs review by a native speaker.
"""

from __future__ import annotations

from hawiyya.contract.enums import REASON_TEXT, DecisionKind
from hawiyya.contract.models import Decision
from hawiyya.matching.levels import LEVEL_LABELS, spec

WHAT = {
    DecisionKind.LINK: ("Recommend a merge request to the health information management office.",
                        "يوصى بإرسال طلب دمج إلى مكتب إدارة المعلومات الصحية."),
    DecisionKind.REVIEW: ("Send this pair to a human reviewer; do not merge automatically.",
                          "أحل هذا الزوج إلى مراجع بشري، ولا تدمجه تلقائيا."),
    DecisionKind.KEEP_APART: ("Keep the two records apart.", "أبق السجلين منفصلين."),
}  # fmt: skip


def explain(d: Decision, next_question: tuple[str, str] | None = None) -> dict[str, list[str]]:
    items = sorted(d.evidence.pair.evidence, key=lambda e: -abs(e.weight))[:2]
    parts_en = []
    parts_ar = []
    for e in items:
        f = spec(e.field)
        lab = LEVEL_LABELS.get(e.level, {"en": e.level, "ar": e.level})
        sign_en = "supports" if e.weight >= 0 else "argues against"
        sign_ar = "يدعم" if e.weight >= 0 else "يعارض"
        parts_en.append(f"{f.label_en} is {lab['en']} ({sign_en} a match)")
        parts_ar.append(f"{f.label_ar}: {lab['ar']} ({sign_ar} التطابق)")
    p = d.evidence.pair.probability
    why_en = f"The calibrated probability is {p:.3f}; " + "; ".join(parts_en) + "."
    why_ar = f"الاحتمال المعاير {p:.3f}؛ " + "؛ ".join(parts_ar) + "."
    if d.guards_fired:
        g = d.guards_fired[0]
        why_en += " Guard: " + REASON_TEXT[g]["en"]
        why_ar += " قاعدة حماية: " + REASON_TEXT[g]["ar"]
    if next_question is not None:
        change_en = f"The most useful next step: {next_question[0].lower()}."
        change_ar = f"الخطوة التالية الأكثر فائدة: {next_question[1]}."
    elif d.decision == DecisionKind.LINK:
        change_en = "A disagreeing card read identifier or date of birth would stop the merge."
        change_ar = "رقم هوية مختلف من قارئ البطاقة أو تاريخ ميلاد مختلف سيوقف الدمج."
    else:
        change_en = "A matching card read identifier would be the strongest new evidence."
        change_ar = "رقم هوية متطابق من قارئ البطاقة سيكون أقوى دليل جديد."
    return {"en": [WHAT[d.decision][0], why_en, change_en],
            "ar": [WHAT[d.decision][1], why_ar, change_ar]}  # fmt: skip
