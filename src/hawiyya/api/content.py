"""Read only content for the console: results, method and limits, claims, provenance."""

from __future__ import annotations

import json
from typing import Any

from hawiyya.core.claims import load_claims
from hawiyya.core.paths import DATA, RESULTS
from hawiyya.lab.predictions import EXPERIMENTS_DIR, judge_all, load_predictions

EXPERIMENT_IDS = ("E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8", "E9", "headline")


def _read(name: str) -> dict[str, Any] | None:
    p = EXPERIMENTS_DIR / f"{name}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def fairness() -> dict[str, Any]:
    return {"dev": _read("E7_dev"), "sealed": _read("E7_sealed"),
            "note": "Origin groups are coarse generator labels used only to stratify results; "
                    "they are never a model input."}  # fmt: skip


def experiments() -> dict[str, Any]:
    preds = {p["id"]: p for p in load_predictions()}
    judged = [{"id": j.prediction_id, "split": j.split, "hit": j.hit,
               "observed": j.observed if not isinstance(j.observed, dict) else json.loads(json.dumps(j.observed)),
               "text": preds[j.prediction_id]["text"], "experiment": preds[j.prediction_id]["experiment"]}
              for j in judge_all()]  # fmt: skip
    sealed = RESULTS / "SEALED_RUN.json"
    return {
        "results": {f"{e}_{s}": _read(f"{e}_{s}") for e in EXPERIMENT_IDS for s in ("dev", "sealed")},
        "predictions": judged,
        "sealed_run": json.loads(sealed.read_text(encoding="utf-8")) if sealed.exists() else None,
    }  # fmt: skip


LIMITS = [
    ("Synthetic data and synthetic errors: every patient, name, identifier and error rate is generated; nothing is validated on a real registry.",
     "بيانات وأخطاء اصطناعية: كل مريض واسم ورقم ونسبة خطأ مولدة، ولم يتحقق أي شيء على سجل حقيقي."),
    ("The generator G1 and the matcher share ideas and an author; G2 is one alternative world by the same author.",
     "المولد G1 والمطابق يشتركان في الأفكار وفي المؤلف؛ والمولد G2 عالم بديل واحد من المؤلف نفسه."),
    ("Synthea's demographics model a United States population, not the UAE's.",
     "تمثل بيانات Synthea السكانية مجتمعا في الولايات المتحدة وليس مجتمع الإمارات."),
    ("The name lexicon is the build agent's reading; Arabic forms of non Arabic names need native review.",
     "معجم الأسماء من إعداد وكيل البناء؛ والصيغ العربية للأسماء غير العربية تحتاج مراجعة من متحدث أصلي."),
    ("Conditional independence between fields is violated; calibration repairs the scale, not the ranking.",
     "افتراض الاستقلال الشرطي بين الحقول غير صحيح؛ والمعايرة تصلح المقياس لا الترتيب."),
    ("Name origin groups are coarse labels used only to stratify results.",
     "مجموعات أصل الأسماء تصنيفات تقريبية تستخدم فقط لتقسيم النتائج."),
    ("Costs are abstract units chosen by the author, not measured harms.",
     "التكاليف وحدات مجردة اختارها المؤلف وليست أضرارا مقيسة."),
    ("The Arabic copy in this console is machine drafted and needs review by a native speaker.",
     "النص العربي في هذه الواجهة مسودة آلية ويحتاج إلى مراجعة من متحدث أصلي."),
]  # fmt: skip

PILOT = [
    ("Agree a purpose, a legal basis and a data protection impact assessment with the data owner's governance office.",
     "الاتفاق على الغرض والأساس النظامي وتقييم أثر حماية البيانات مع مكتب الحوكمة لدى مالك البيانات."),
    ("Run Hawiyya inside the owner's environment on a de identified extract: registration fields only, identifiers hashed with a key the owner holds.",
     "تشغيل هوية داخل بيئة المالك على مستخرج منزوع الهوية: حقول التسجيل فقط، والأرقام مجزأة بمفتاح يحتفظ به المالك."),
    ("Have health information management staff label a stratified sample of pairs (including hard negatives) without seeing Hawiyya's output.",
     "أن يصنف موظفو إدارة المعلومات الصحية عينة طبقية من الأزواج (ومنها الحالات الصعبة) دون رؤية مخرجات هوية."),
    ("Refit calibration on that sample, preregister predictions, and evaluate on a held out part once.",
     "إعادة المعايرة على تلك العينة، وتسجيل التوقعات مسبقا، والتقييم على جزء محجوز مرة واحدة."),
    ("Keep Hawiyya read only and advisory: every merge stays a request reviewed by a person.",
     "إبقاء هوية للقراءة فقط واستشارية: يبقى كل دمج طلبا يراجعه شخص."),
]  # fmt: skip


def method() -> dict[str, Any]:
    claims = load_claims()
    return {
        "advisory": "Advisory software for planning and learning. It controls nothing.",
        "assumptions": [{"id": c.id, "text": c.text, "where": c.where} for c in claims
                        if c.type == "ASSUMPTION"],
        "limitations": [{"en": en, "ar": ar} for en, ar in LIMITS],
        "independence_contract": "G2 may not import hawiyya.normalise, hawiyya.registry.g1, "
        "hawiyya.matching or hawiyya.scoring; an import contract test enforces it.",
        "label_isolation": "L2 to L5 may import only the registration view; truth labels never "
        "reach normalisation, matching, scoring or decisions.",
        "pilot_path": [{"en": en, "ar": ar} for en, ar in PILOT],
        "arabic_note": {"en": "The Arabic copy is machine drafted and needs review by a native speaker.",
                        "ar": "النص العربي مسودة آلية ويحتاج إلى مراجعة من متحدث أصلي."},
    }  # fmt: skip


def claims() -> dict[str, Any]:
    return {"claims": [vars(c) for c in load_claims()]}


def provenance() -> dict[str, Any]:
    manifest = json.loads((DATA / "MANIFEST.json").read_text(encoding="utf-8"))
    fit = json.loads((RESULTS / "model" / "fit_report.json").read_text(encoding="utf-8"))
    prov = manifest["provenance"]
    return {
        "data_source": manifest["data_source_label"],
        "synthea_release": prov.get("release_tag"), "synthea_jar_sha256": prov.get("jar_sha256"),
        "reference_date": prov.get("reference_date"), "lexicon_author": manifest["lexicon_author"],
        "files_sha256": manifest["files_sha256"],
        "model_version": fit.get("model_version"), "fit_seeds": fit["fit_seeds"],
        "check_seeds": fit["check_seeds"], "estimator": fit["product_estimator"],
    }  # fmt: skip
