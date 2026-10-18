"""P8 evaluation tests: results exist, documents agree with them, predictions came first."""

from __future__ import annotations

import json
import re
import subprocess

import pytest

from hawiyya.cli.docs_build import BLOCKS, apply_blocks
from hawiyya.core.paths import DOCS, RESULTS, ROOT
from hawiyya.lab.predictions import judge_all, load_predictions

EXPERIMENTS = ("E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8", "E9", "headline")


@pytest.mark.req("HW-L7-009")
def test_experiment_results_exist() -> None:
    for e in EXPERIMENTS:
        doc = json.loads((RESULTS / "experiments" / f"{e}_dev.json").read_text(encoding="utf-8"))
        assert doc["experiment"] == e and doc["split"] == "dev"
        assert "synthetic" in doc["note"].lower()


@pytest.mark.req("HW-X-011")
def test_evaluation_document_matches_results() -> None:
    path = DOCS / "EVALUATION.md"
    text = path.read_text(encoding="utf-8")
    assert apply_blocks(text, BLOCKS[path]) == text, "run `hawiyya docs build`"
    # Outside generated blocks the prose carries no measured numbers.
    prose = re.sub(r"<!-- BEGIN:(\w+) -->.*?<!-- END:\1 -->", "", text, flags=re.DOTALL)
    assert not re.findall(r"\d+\.\d+", prose)


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True,
                          check=True).stdout.strip()  # fmt: skip


@pytest.mark.req("HW-L7-010")
def test_predictions_committed_before_results_and_judged() -> None:
    try:
        pred_commits = _git("log", "--format=%H", "--", "spec/predictions.json").split()
        res_commits = _git("log", "--reverse", "--format=%H", "--", "results/experiments").split()
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("git history unavailable")
    if not res_commits:
        pytest.skip("no experiment results committed yet")
    first_results = res_commits[0]
    for c in pred_commits:
        ok = subprocess.run(["git", "merge-base", "--is-ancestor", c, first_results], cwd=ROOT)
        assert ok.returncode == 0, f"predictions changed after results ({c[:8]})"
    ids = {p["id"] for p in load_predictions()}
    judged = {j.prediction_id for j in judge_all() if j.split == "dev" and j.hit is not None}
    assert judged == ids
