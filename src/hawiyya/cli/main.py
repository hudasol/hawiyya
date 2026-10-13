"""Hawiyya command line interface."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import typer

from hawiyya.core.paths import ROOT

app = typer.Typer(add_completion=False, no_args_is_help=True, help="Hawiyya command line.")
docs_app = typer.Typer(add_completion=False, help="Generated documents.")
app.add_typer(docs_app, name="docs")


def _tool(name: str) -> str:
    """Find a console script next to the running interpreter, then on PATH."""
    scripts = Path(sys.executable).parent
    for candidate in (scripts / f"{name}.exe", scripts / name):
        if candidate.exists():
            return str(candidate)
    found = shutil.which(name)
    if not found:
        raise typer.Exit(code=2)
    return found


def _run(label: str, cmd: list[str], timeout: int) -> bool:
    start = time.perf_counter()
    env = dict(os.environ, PYTHONUTF8="1", CI="1")
    try:
        proc = subprocess.run(
            cmd, cwd=ROOT, env=env, timeout=timeout, capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
    except subprocess.TimeoutExpired:
        typer.echo(f"[FAIL] {label}: timed out after {timeout}s")
        return False
    ok = proc.returncode == 0
    secs = time.perf_counter() - start
    typer.echo(f"[{'ok' if ok else 'FAIL'}] {label} ({secs:.1f}s)")
    if not ok:
        tail = (proc.stdout + proc.stderr).strip().splitlines()[-40:]
        typer.echo("\n".join(tail))
    return ok


@app.command()
def check(full: bool = typer.Option(False, help="Also run slow tests.")) -> None:
    """Fast check: lint, types, import contracts, unit tests, traceability."""
    from hawiyya.cli.docs_build import build_all

    stale = build_all(write=True)
    for path in stale:
        typer.echo(f"[info] regenerated {path.relative_to(ROOT).as_posix()}")
    py = sys.executable
    pytest_cmd = [py, "-m", "pytest", "-x"] + ([] if full else ["-m", "not slow"])
    steps = [
        ("ruff", [_tool("ruff"), "check", "src", "tests"], 120),
        ("mypy --strict", [py, "-m", "mypy", "src"], 600),
        ("import contracts", [_tool("lint-imports"), "--no-cache"], 120),
        ("pytest", pytest_cmd, 1800),
    ]
    results = [_run(label, cmd, timeout) for label, cmd, timeout in steps]
    if not all(results):
        raise typer.Exit(code=1)
    typer.echo("check passed")


@docs_app.command("build")
def docs_build() -> None:
    """Render generated documents (traceability matrix, claims register, results pages)."""
    from hawiyya.cli.docs_build import build_all

    stale = build_all(write=True)
    typer.echo(f"rendered; {len(stale)} file(s) changed")


if __name__ == "__main__":
    app()
