"""P0 harness tests: traceability, claims, generated documents, repository hygiene."""

from __future__ import annotations

import subprocess
import sys

import pytest

from hawiyya.cli.docs_build import build_all
from hawiyya.core import claims, traceability
from hawiyya.core.paths import ROOT
from hawiyya.core.safelog import is_safe_value, safe_event


@pytest.mark.req("HW-X-005")
def test_every_enforced_must_has_a_test() -> None:
    reqs = traceability.load_requirements()
    refs = traceability.test_references()
    phase = traceability.enforced_phase()
    missing = traceability.untested_musts(reqs, refs, phase)
    assert missing == [], f"MUST requirements without a naming test: {missing}"


@pytest.mark.req("HW-X-006")
def test_every_claim_pointer_resolves() -> None:
    bad = [c.id for c in claims.load_claims() if not claims.resolve(c)]
    assert bad == []


def test_claim_pointer_failure_is_detected() -> None:
    fake = claims.Claim("CL-999", "x", "SUPPORTED_BY_RESULT", "result", "results/none.json#/a", "-")
    assert not claims.resolve(fake)
    fake2 = claims.Claim("CL-998", "x", "ASSUMPTION", "param", "hawiyya.core.paths:NOPE", "-")
    assert not claims.resolve(fake2)


@pytest.mark.req("HW-X-012")
def test_generated_documents_are_fresh() -> None:
    stale = build_all(write=False)
    assert stale == [], f"run `hawiyya docs build`: {stale}"


def _tracked_text_files() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT, capture_output=True, check=True,
    ).stdout.decode("utf-8")
    binary = (".png", ".gz", ".woff", ".woff2", ".jpg", ".ico", ".lock")
    return [f for f in out.split("\0") if f and not f.endswith(binary)]


@pytest.mark.req("HW-X-007")
def test_no_em_dash_in_tracked_files() -> None:
    em = chr(0x2014)
    offenders = []
    for f in _tracked_text_files():
        p = ROOT / f
        if not p.is_file():
            continue
        if em in p.read_text(encoding="utf-8", errors="ignore"):
            offenders.append(f)
    assert offenders == []


# Terms are stored reversed so this file does not itself contain them.
_FORBIDDEN_ANYWHERE = ["ytisrevinu"]
_AUTHORITY_TERMS = [
    "AHD", "htlaeH fo tnemtrapeD", "yhtirohtuA htlaeH iabuD", "HDIBAN", "iaffalaM",
    "htlaeH fo yrtsiniM", "HOD",
]
_CONTEXT_ONLY = {"docs/CONTEXT.md"}


@pytest.mark.req("HW-X-008")
def test_no_affiliation_and_no_authority_outside_context() -> None:
    import re

    anywhere = [t[::-1].lower() for t in _FORBIDDEN_ANYWHERE]
    authority = [re.compile(r"\b" + re.escape(t[::-1]) + r"\b") for t in _AUTHORITY_TERMS]
    offenders = []
    for f in _tracked_text_files():
        p = ROOT / f
        if not p.is_file() or f.startswith("inputs/cowork/") or f == "LICENSE":
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        if any(t in text.lower() for t in anywhere):
            offenders.append(f)
        if f not in _CONTEXT_ONLY and any(rx.search(text) for rx in authority):
            offenders.append(f)
    assert offenders == []


@pytest.mark.req("HW-X-010")
def test_safe_log_refuses_names_and_identifiers() -> None:
    assert safe_event("pair_scored", record_a="r000123", n=3).startswith("pair_scored")
    for bad in ["Mohammed Al Mazrouei", "784199012345671", "محمد", "a b"]:
        assert not is_safe_value(bad)
        with pytest.raises(ValueError):
            safe_event("x", value=bad)


@pytest.mark.req("HW-X-001")
def test_cli_check_command_is_registered() -> None:
    from typer.testing import CliRunner

    from hawiyya.cli.main import app

    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "check" in result.stdout


@pytest.mark.req("HW-X-002", "HW-X-003", "HW-X-004")
def test_import_contracts_hold() -> None:
    from pathlib import Path

    scripts = Path(sys.executable).parent
    exe = next(p for p in (scripts / "lint-imports.exe", scripts / "lint-imports") if p.exists())
    proc = subprocess.run([str(exe), "--no-cache"], cwd=ROOT, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout[-2000:]
    for name in ("Layers point downward", "Independence", "Label isolation"):
        assert name in proc.stdout
