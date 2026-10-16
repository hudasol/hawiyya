"""Name lab service: normalised forms, structure, keys, generator variants and comparison."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from hawiyya.core.determinism import rng
from hawiyya.lab.lexicon_report import build_report
from hawiyya.matching.compare import features
from hawiyya.matching.levels import FIELD_INDEX, FIELDS, LEVEL_LABELS
from hawiyya.normalise.names import parse_name
from hawiyya.normalise.record import normalise_record
from hawiyya.normalise.text import coarse_key, has_arabic, normalize_text, script_of, skeleton_word
from hawiyya.registry.g1.translit import translit_name
from hawiyya.registry.lexicon import default_lexicon
from hawiyya.registry.view import Record


@lru_cache(maxsize=1)
def _collision_groups() -> list[list[str]]:
    groups: list[list[str]] = build_report(default_lexicon())["skeleton"]["collision_groups"]
    return groups


def _lexicon_variants(name: str) -> list[str]:
    """Spellings the lexicon lists for tokens of this name (generator side knowledge)."""
    lex = default_lexicon()
    keys = {skeleton_word(t) for t in normalize_text(name).split()}
    out: list[str] = []
    for e in (*lex.given, *lex.family):
        ek = {skeleton_word(t) for t in normalize_text(e.canonical_latin).split()}
        if ek & keys and len(out) < 12:
            out.extend(v for v in e.latin if v not in out)
    return out[:12]


def analyse(name: str, other: str | None = None) -> dict[str, Any]:
    p = parse_name(name)
    tokens = list(p.tokens) if p else []
    out: dict[str, Any] = {
        "input_script": script_of(name),
        "normalised": normalize_text(name),
        "tokens": [
            {"token": t, "skeleton": skeleton_word(t), "coarse": coarse_key(skeleton_word(t))}
            for t in tokens
        ],
        "structure": {
            "given": p.given if p else None,
            "father": p.father if p else None,
            "grandfather": p.grandfather if p else None,
            "family": p.family if p else None,
            "initials": sorted(p.initials) if p else [],
            "connector": p.had_connector if p else False,
        },
        "generator_variants": {},
        "collisions": [],
    }
    if has_arabic(name):
        g = rng(0, "name_lab", name)
        out["generator_variants"] = {
            style: sorted({translit_name(normalize_text(name), g, style) for _ in range(6)})
            for style in ("formal", "gulf", "arabizi")
        }
    else:
        out["generator_variants"] = {"lexicon": _lexicon_variants(name)}
    keys = {skeleton_word(t) for t in tokens}
    for grp in _collision_groups():
        gk = {skeleton_word(normalize_text(x).split()[-1]) for x in grp}
        if gk & keys:
            out["collisions"].append(grp)
    if other:
        out["comparison"] = compare_names(name, other)
    return out


def compare_names(a: str, b: str) -> dict[str, Any]:
    def rec(n: str, rid: str) -> Record:
        field = "name_ar" if has_arabic(n) else "name_latin"
        return Record.model_validate({"record_id": rid, "facility_id": "LAB", field: n,
                                      "registered_on": "2026-01-01"})

    from hawiyya.matching.compare import compare_pair

    lv = compare_pair(features(normalise_record(rec(a, "a"))),
                      features(normalise_record(rec(b, "b"))))
    res = {}
    for name in ("given", "family", "father", "whole_name"):
        level = FIELDS[FIELD_INDEX[name]].levels[int(lv[FIELD_INDEX[name]])]
        res[name] = {"level": level, "label_en": LEVEL_LABELS[level]["en"],
                     "label_ar": LEVEL_LABELS[level]["ar"]}  # fmt: skip
    return res
