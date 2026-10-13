"""Repository paths, resolved from the installed source tree."""

from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    """Return the repository root (the folder that holds ``pyproject.toml``)."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pyproject.toml").is_file() and (parent / "src").is_dir():
            return parent
    raise RuntimeError("repository root not found above " + str(here))


ROOT = repo_root()
DATA = ROOT / "data"
DOCS = ROOT / "docs"
RESULTS = ROOT / "results"
SPEC = ROOT / "spec"
CONTRACT_DIR = ROOT / "contract"
WEB = ROOT / "web"
VAR = ROOT / "var"
PRIVATE = ROOT / ".sikka"
