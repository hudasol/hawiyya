"""Render generated documents from their sources."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from hawiyya.core import claims, traceability

Renderer = Callable[[], tuple[Path, str]]


def _traceability() -> tuple[Path, str]:
    reqs = traceability.load_requirements()
    refs = traceability.test_references()
    phase = traceability.enforced_phase()
    return traceability.matrix_path(), traceability.render_matrix(reqs, refs, phase)


def _claims() -> tuple[Path, str]:
    return claims.register_path(), claims.render_register(claims.load_claims())


RENDERERS: list[Renderer] = [_traceability, _claims]


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
