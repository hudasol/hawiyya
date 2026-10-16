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
            cmd,
            cwd=ROOT,
            env=env,
            timeout=timeout,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
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


data_app = typer.Typer(add_completion=False, help="Synthetic data: source, manifest, reports.")
app.add_typer(data_app, name="data")


@data_app.command("synthea")
def data_synthea(
    population: int = typer.Option(25000, help="Synthea population size."),
    seed: int = typer.Option(20261013, help="First chunk seed."),
    chunk: int = typer.Option(2500, help="Patients per deterministic chunk."),
) -> None:
    """Download Synthea, run it in deterministic chunks and derive the committed sample."""
    from hawiyya.core.paths import PRIVATE
    from hawiyya.registry import synthea

    meta = synthea.fetch_jar(PRIVATE / "tools")
    synthea.run_chunks(Path(meta["path"]), PRIVATE / "synthea", seed, population, chunk, 3600)
    data_manifest(source="synthea")


@data_app.command("manifest")
def data_manifest(source: str = typer.Option("synthea", help="synthea or native")) -> None:
    """Write data/MANIFEST.json (deriving the Synthea sample when the source is Synthea)."""
    from hawiyya.registry import manifest
    from hawiyya.registry.lexicon import default_lexicon

    if source == "synthea":
        prov = manifest.derive_synthea_sample()
    else:
        prov = {"generator": "hawiyya.registry.source.native_population", "pool_seed": 20261013}
    cowork = {"present": (ROOT / "inputs" / "cowork").is_dir()}
    manifest.write_manifest(source, prov, default_lexicon().author, cowork)
    typer.echo(f"manifest written; data source {source}")


@data_app.command("lexicon-report")
def data_lexicon_report() -> None:
    """Measure skeleton collisions in the lexicon and write results/lexicon_report.json."""
    from hawiyya.lab.lexicon_report import write_report
    from hawiyya.registry.lexicon import default_lexicon

    rep = write_report(default_lexicon())
    typer.echo(f"skeleton collision rate {rep['skeleton']['collision_rate']}")


lab_app = typer.Typer(add_completion=False, help="Lab reports and experiments.")
app.add_typer(lab_app, name="lab")


@lab_app.command("placeholders")
def lab_placeholders() -> None:
    """Evaluate placeholder detectors on development seeds (results/placeholder_detector.json)."""
    from hawiyya.lab.placeholder_report import write_report

    rep = write_report()
    learned = [s["value_level"]["learned"] for s in rep["per_seed"]]
    typer.echo(f"learned detector precision/recall per seed: "
               f"{[(x['precision'], x['recall']) for x in learned]}")


@lab_app.command("blocking-smoke")
def lab_blocking_smoke() -> None:
    """Development smoke check of blocking (results/dev/blocking_smoke.json)."""
    from hawiyya.lab.blocking_smoke import write

    rep = write()
    typer.echo(f"pair completeness {rep['pair_completeness']}, "
               f"reduction ratio {rep['reduction_ratio']}")


@lab_app.command("train")
def lab_train() -> None:
    """Fit and freeze the scoring model on development seeds (results/model/)."""
    from hawiyya.lab.train import write

    rep = write()
    typer.echo(f"plain EM lambda {rep['plain_em']['lambda']}, anchored lambda "
               f"{rep['em_anchored']['lambda']}, labels {rep['labels']['lambda']}; "
               f"ECE on check seeds {rep['calibration_check']['ece_product']}")


contract_app = typer.Typer(add_completion=False, help="L0 contract artefacts.")
app.add_typer(contract_app, name="contract")


@contract_app.command("generate")
def contract_generate() -> None:
    """Regenerate JSON Schema, TypeScript types and the bilingual field dictionary."""
    from hawiyya.contract.codegen import write_artefacts

    written = write_artefacts()
    typer.echo(f"generated; {len(written)} file(s) changed")


@docs_app.command("build")
def docs_build() -> None:
    """Render generated documents (traceability matrix, claims register, results pages)."""
    from hawiyya.cli.docs_build import build_all

    stale = build_all(write=True)
    typer.echo(f"rendered; {len(stale)} file(s) changed")


if __name__ == "__main__":
    app()
