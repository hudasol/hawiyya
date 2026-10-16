"""Render generated documents from their sources.

Two kinds of output: whole generated files (traceability matrix, claims register, results
pages) and generated blocks inside hand written files, delimited by
``<!-- BEGIN:name -->`` and ``<!-- END:name -->``.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path

from hawiyya.core import claims, traceability
from hawiyya.core.paths import DOCS, ROOT

Renderer = Callable[[], tuple[Path, str]]
BlockFn = Callable[[], str]


def _traceability() -> tuple[Path, str]:
    reqs = traceability.load_requirements()
    refs = traceability.test_references()
    phase = traceability.enforced_phase()
    return traceability.matrix_path(), traceability.render_matrix(reqs, refs, phase)


def _claims() -> tuple[Path, str]:
    return claims.register_path(), claims.render_register(claims.load_claims())


def data_source_block() -> str:
    from hawiyya.registry.manifest import load_manifest

    m = load_manifest()
    lines = [f"Data source: {m['data_source_label']}", ""]
    prov = m["provenance"]
    if m["data_source"] == "synthea":
        lines += [
            f"- Synthea release tag `{prov['release_tag']}`, jar SHA 256 `{prov['jar_sha256']}`.",
            f"- {len(prov['chunks'])} deterministic runs, reference date {prov['reference_date']},"
            f" {prov['alive_patients_kept']} living synthetic patients kept.",
            "- Kept columns: " + ", ".join(f"`{c}`" for c in prov["columns_kept"]) + ".",
        ]
    else:
        lines.append("- Native generator in `hawiyya.registry.source.native_population`.")
    lines.append(f"- Name lexicon author: `{m['lexicon_author']}`.")
    lines.append("- Exact commands and file hashes: `data/MANIFEST.json`.")
    return "\n".join(lines)


BLOCKS: dict[Path, dict[str, BlockFn]] = {
    ROOT / "README.md": {"data_source": data_source_block},
    DOCS / "DATA_STATEMENT.md": {"data_source": data_source_block},
}


def apply_blocks(text: str, blocks: dict[str, BlockFn]) -> str:
    for name, fn in blocks.items():
        pattern = re.compile(
            rf"(<!-- BEGIN:{name} -->\n).*?(<!-- END:{name} -->)", flags=re.DOTALL
        )
        if not pattern.search(text):
            raise ValueError(f"block {name} not found")
        body = fn().rstrip("\n") + "\n"
        text = pattern.sub(lambda m, b=body: m.group(1) + b + m.group(2), text)  # type: ignore[misc]
    return text


def _block_renderer(path: Path) -> Renderer:
    def render() -> tuple[Path, str]:
        return path, apply_blocks(path.read_text(encoding="utf-8"), BLOCKS[path])

    return render


RENDERERS: list[Renderer] = [_traceability, _claims] + [_block_renderer(p) for p in BLOCKS]


def register(renderer: Renderer) -> None:
    """Add a renderer (used by higher layers that render documents from results)."""
    if renderer not in RENDERERS:
        RENDERERS.append(renderer)


def build_all(write: bool = True) -> list[Path]:
    """Render every generated document. Return the paths that were stale."""
    stale: list[Path] = []
    for renderer in RENDERERS:
        path, text = renderer()
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current != text:
            stale.append(path)
            if write:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8", newline="\n")
    return stale
