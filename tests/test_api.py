"""L8 API tests (live mode with the demonstration registry) and the registration check."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from hawiyya.api.app import app
from hawiyya.api.state import get_state
from hawiyya.workflow.check import run_check

PROBLEM = "application/problem+json"


@pytest.fixture(scope="module")
def client() -> TestClient:
    get_state()  # build once
    return TestClient(app)


@pytest.mark.req("HW-L8-001")
def test_walking_skeleton_endpoints(client: TestClient) -> None:
    h = client.get("/v1/health").json()
    assert h["status"] == "ok" and "synthetic" in h["synthetic_note"]
    s = client.get("/v1/registry/summary").json()
    assert s["records"] > 1000
    assert s["synthetic_ground_truth"]["label"] == "synthetic ground truth"
    c = client.post("/v1/check", json={"name_latin": "Mohammed Ali", "dob": "1990-01-02"})
    assert c.status_code == 200 and c.json()["ok"] is True
    n = client.post("/v1/names/analyse", json={"name": "Abdul Rahman Al Kaabi",
                                               "other": "عبدالرحمن الكعبي"})
    body = n.json()
    assert body["structure"]["given"] == "abdulrahman"
    assert body["comparison"]["given"]["level"] == "skeleton"


@pytest.mark.req("HW-L8-003")
def test_errors_are_problem_json(client: TestClient) -> None:
    r = client.post("/v1/check", json={"name_latin": "x", "unknown_field": 1})
    assert r.status_code == 422 and r.headers["content-type"].startswith(PROBLEM)
    assert r.json()["title"] == "Invalid request"
    r = client.get("/v1/nothing-here")
    assert r.status_code == 404 and r.headers["content-type"].startswith(PROBLEM)


@pytest.mark.req("HW-L8-004")
def test_inputs_are_bounded(client: TestClient) -> None:
    r = client.post("/v1/names/analyse", json={"name": "a" * 500})
    assert r.status_code == 422
    big = "x" * (17 * 1024)
    r = client.post("/v1/names/analyse", content=json.dumps({"name": big}),
                    headers={"content-type": "application/json"})
    assert r.status_code == 413 and r.headers["content-type"].startswith(PROBLEM)
    r = client.post("/v1/check", json={"name_latin": "A", "top": 500})
    assert r.status_code == 422


@pytest.mark.req("HW-L6-004")
def test_existing_record_is_returned_first(client: TestClient) -> None:
    st = get_state()
    target = next(r for r in st.registry.records if r.name_latin and r.dob and r.id_value
                  and r.id_kind is not None and r.id_kind.value == "EID")
    body = {k: v for k, v in target.model_dump(mode="json").items()
            if k in ("name_ar", "name_latin", "sex", "dob", "id_value", "id_kind", "id_capture",
                     "nationality", "phone", "area")}  # fmt: skip
    res = client.post("/v1/check", json=body).json()
    assert res["candidates"][0]["record"]["record_id"] == target.record_id


@pytest.mark.req("HW-L6-009")
def test_check_fails_open() -> None:
    st = get_state()
    rec = st.registry.records[0]
    res = run_check(st.index, None, rec)  # type: ignore[arg-type]
    assert res.ok is False and res.candidates == ()
    assert "registration continues" in res.note


@pytest.mark.req("HW-L8-005")
def test_static_snapshot(tmp_path: Path) -> None:
    from hawiyya.api.snapshot import build_snapshot

    files = build_snapshot(tmp_path)
    names = {f.name for f in files}
    assert {"health.json", "registry_summary.json", "check_examples.json",
            "names_examples.json"} <= names
    ex = json.loads((tmp_path / "check_examples.json").read_text(encoding="utf-8"))
    assert ex["mode"] == "static" and len(ex["examples"]) >= 4
    for e in ex["examples"]:
        assert e["response"]["synthetic_note"]
