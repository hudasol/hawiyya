"""Static snapshot: precompute every response the console needs, for a backend free demo."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from hawiyya.api import service
from hawiyya.api.schemas import NameInput, RegistrationInput
from hawiyya.api.state import get_state
from hawiyya.core.paths import WEB

SNAPSHOT_DIR = WEB / "public" / "snapshot"
NAME_EXAMPLES = ("محمد بن راشد المنصوري", "Mohd Rashid Almansoori", "mo7amed rashed",
                 "Abdul Rahman Al Kaabi", "Hassan Ali", "Priya Sharma")  # fmt: skip


def _example_inputs() -> list[tuple[str, str, RegistrationInput]]:
    """Pick demonstration inputs from the demo registry by registration style."""
    st = get_state()
    out: list[tuple[str, str, RegistrationInput]] = []
    want = {
        "arabizi": ("arabizi_name", "Arabizi name and date of birth, no identifier"),
        "formal_ar": ("arabic_only", "Arabic script name only, with date of birth"),
        "bilingual_card": ("card_read", "Card read registration with identifier"),
    }
    seen: set[str] = set()
    for r in st.registry.records:
        style = st.registry.truth.labels[r.record_id].name_style
        if style in want and style not in seen and r.dob and r.sex:
            key, label = want[style]
            seen.add(style)
            out.append((key, label, RegistrationInput(
                name_ar=r.name_ar if style != "arabizi" else None,
                name_latin=r.name_latin if style != "formal_ar" else None,
                sex=r.sex, dob=r.dob,
                id_value=r.id_value if style == "bilingual_card" else None,
                id_kind=r.id_kind if style == "bilingual_card" else None,
                id_capture=r.id_capture if style == "bilingual_card" else None,
            )))  # fmt: skip
    out.append(("common_name_only", "A very common name with nothing else",
                RegistrationInput(name_latin="Mohammed Ali")))
    out.append(("placeholder_id", "Placeholder identifier with a common name",
                RegistrationInput(name_latin="Ahmed Hassan", id_value="111111111111111",
                                  id_kind="PLACEHOLDER", id_capture="placeholder")))
    return out


def build_snapshot(out_dir: Path = SNAPSHOT_DIR) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    files: dict[str, Any] = {
        "health.json": {**service.health(), "mode": "static"},
        "registry_summary.json": {**service.registry_summary(), "mode": "static"},
    }
    examples = []
    for key, label, inp in _example_inputs():
        res = service.check(inp).model_dump(mode="json")
        res["mode"] = "static"
        examples.append({"key": key, "label": label, "input": inp.model_dump(mode="json"),
                         "response": res})  # fmt: skip
    files["check_examples.json"] = {"mode": "static", "examples": examples}
    files["names_examples.json"] = {
        "mode": "static",
        "examples": [{"name": n, "response": service.names_analyse(NameInput(name=n))}
                     for n in NAME_EXAMPLES],
    }  # fmt: skip
    written = []
    for name, payload in files.items():
        p = out_dir / name
        p.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8",
                     newline="\n")
        written.append(p)
    return written
