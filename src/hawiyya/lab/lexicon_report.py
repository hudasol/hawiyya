"""Lexicon quality report: how often distinct names collide on the skeleton or coarse key."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from hawiyya.core.paths import RESULTS
from hawiyya.normalise.names import parse_name
from hawiyya.normalise.text import coarse_key, string_skeleton
from hawiyya.registry.lexicon import Lexicon, NameEntry


def _collisions(entries: list[NameEntry], key: str) -> dict[str, Any]:
    groups: dict[str, set[str]] = defaultdict(set)
    for e in entries:
        k = string_skeleton(e.canonical_latin)
        if key == "coarse":
            k = coarse_key(k)
        groups[k].add(e.canonical_latin)
    names = {e.canonical_latin for e in entries}
    colliding = {n for g in groups.values() if len(g) > 1 for n in g}
    examples = sorted(sorted(g) for g in groups.values() if len(g) > 1)
    return {
        "distinct_names": len(names),
        "colliding_names": len(colliding),
        "collision_rate": round(len(colliding) / len(names), 4) if names else 0.0,
        "collision_groups": examples,
    }


def _variant_agreement(entries: list[NameEntry]) -> dict[str, Any]:
    """Share of listed spellings (Latin variants and the Arabic form) whose skeleton equals
    the canonical spelling's skeleton."""
    total = agree = 0
    misses: list[list[str]] = []
    for e in entries:
        base = string_skeleton(e.canonical_latin)
        for v in (*e.latin[1:], e.ar):
            total += 1
            if string_skeleton(v) == base:
                agree += 1
            elif len(misses) < 40 and v != e.ar:
                misses.append([e.canonical_latin, v])
    return {"spellings": total, "same_skeleton": agree,
            "share": round(agree / total, 4) if total else 0.0, "latin_misses": misses}


def _model_key(text: str, family: bool) -> str:
    """Key from the person name model (handles glued articles and compound names)."""
    parsed = parse_name(("x " + text) if family else text)
    if parsed is None:
        return ""
    return parsed.family_key if family else parsed.given_key


def _name_model_agreement(lex: Lexicon) -> dict[str, Any]:
    total = agree = 0
    for entries, fam in ((lex.given, False), (lex.family, True)):
        for e in entries:
            base = _model_key(e.canonical_latin, fam)
            for v in (*e.latin[1:], e.ar):
                total += 1
                agree += _model_key(v, fam) == base
    return {"spellings": total, "same_key": agree,
            "share": round(agree / total, 4) if total else 0.0}


def build_report(lex: Lexicon) -> dict[str, Any]:
    by_canon: dict[str, NameEntry] = {}
    for e in (*lex.given, *lex.family):
        by_canon.setdefault(e.canonical_latin, e)
    entries = list(by_canon.values())
    return {
        "lexicon_author": lex.author,
        "definition": "collision_rate is the share of distinct canonical lexicon names (given "
        "and family names together) that share a skeleton key with at least one other "
        "distinct name.",
        "skeleton": _collisions(entries, "skeleton"),
        "coarse_key": _collisions(entries, "coarse"),
        "given_only": _collisions(list(lex.given), "skeleton"),
        "variant_agreement": _variant_agreement(entries),
        "variant_agreement_name_model": _name_model_agreement(lex),
    }


def write_report(lex: Lexicon, path: Path | None = None) -> dict[str, Any]:
    report = build_report(lex)
    out = path or RESULTS / "lexicon_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8",
                   newline="\n")
    return report
