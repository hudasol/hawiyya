"""Every /v1 endpoint has a test (HW-L8-002); server logs carry no names (HW-L8-007)."""

from __future__ import annotations

import logging

import pytest
from fastapi.testclient import TestClient

from hawiyya.api.app import app
from hawiyya.api.state import get_state
from hawiyya.normalise.identifiers import is_pattern_placeholder
from hawiyya.workflow.export import validate_bundle

PROBLEM = "application/problem+json"
ROUTES = {"/v1/health", "/v1/registry/summary", "/v1/check", "/v1/score", "/v1/review/queue",
          "/v1/review/{case_id}", "/v1/review/{case_id}/action", "/v1/clusters",
          "/v1/clusters/{cluster_id}", "/v1/placeholders", "/v1/names/analyse",
          "/v1/thresholds/curve", "/v1/thresholds/simulate", "/v1/fairness", "/v1/experiments",
          "/v1/method", "/v1/claims", "/v1/provenance", "/v1/export/fhir/{cluster_id}",
          "/v1/audit"}  # fmt: skip


@pytest.fixture(scope="module")
def client() -> TestClient:
    get_state()
    return TestClient(app)


@pytest.mark.req("HW-L8-002")
def test_every_listed_endpoint_exists() -> None:
    paths = {getattr(r, "path", "") for r in app.routes}
    assert paths >= ROUTES


@pytest.mark.req("HW-L8-002")
def test_review_endpoints(client: TestClient) -> None:
    q = client.get("/v1/review/queue?limit=5").json()
    assert q["cases"] and "workload" in q and q["synthetic_note"]
    cid = q["cases"][0]["case_id"]
    case = client.get(f"/v1/review/{cid}").json()
    assert len(case["records"]) == 2 and case["next_best_question"]
    assert len(case["decision_detail"]["explanation"]["en"]) == 3
    r = client.post(f"/v1/review/{cid}/action", json={"action": "request_merge"})
    assert r.status_code == 409 and r.headers["content-type"].startswith(PROBLEM)
    r = client.post(f"/v1/review/{cid}/action", json={"action": "assign"})
    assert r.status_code == 200 and r.json()["state"] == "ASSIGNED"
    assert client.get("/v1/review/C0000000000").status_code == 404
    assert client.get("/v1/review/not-an-id").status_code == 422


@pytest.mark.req("HW-L8-002")
def test_cluster_and_export_endpoints(client: TestClient) -> None:
    cl = client.get("/v1/clusters?limit=3").json()
    assert cl["clusters"]
    cid = cl["clusters"][0]["cluster_id"]
    detail = client.get(f"/v1/clusters/{cid}").json()
    assert detail["records"] and detail["statement"]
    bundle = client.get(f"/v1/export/fhir/{cid}").json()
    validate_bundle(bundle)
    assert client.get("/v1/clusters/K9999").status_code == 404


@pytest.mark.req("HW-L8-002")
def test_placeholder_and_threshold_endpoints(client: TestClient) -> None:
    ph = client.get("/v1/placeholders").json()
    assert ph["truth_label"] == "synthetic ground truth"
    assert any(r["pattern"] for r in ph["identifiers"])
    curve = client.get("/v1/thresholds/curve").json()
    assert curve["risk_coverage"] and curve["default"]["thresholds"]["t_link"] == pytest.approx(0.996)
    sim = client.post("/v1/thresholds/simulate", json={"c_fm": 2000, "c_md": 20, "c_r": 2}).json()
    base = curve["default"]
    assert sim["review_rate_per_1000"] >= base["review_rate_per_1000"]
    assert client.post("/v1/thresholds/simulate", json={"c_fm": -1, "c_md": 1, "c_r": 1}).status_code == 422


@pytest.mark.req("HW-L8-002")
def test_content_endpoints(client: TestClient) -> None:
    for path in ("/v1/fairness", "/v1/experiments", "/v1/method", "/v1/claims",
                 "/v1/provenance", "/v1/audit"):
        r = client.get(path)
        assert r.status_code == 200, path
        assert r.json()["synthetic_note"]
    m = client.get("/v1/method").json()
    assert m["pilot_path"] and m["limitations"] and m["arabic_note"]["ar"]
    a = client.get("/v1/audit").json()
    assert a["chain_ok"] is True
    p = client.post("/v1/score", json={"a": {"name_latin": "Ahmed Ali", "dob": "1990-01-02"},
                                       "b": {"name_latin": "Ahmad Ali", "dob": "1990-01-02"}}).json()
    assert p["decision"]["decision"] in ("LINK", "REVIEW", "KEEP_APART")


@pytest.mark.req("HW-L8-007")
def test_server_logs_hold_no_names_or_identifiers(client: TestClient, caplog) -> None:  # type: ignore[no-untyped-def]
    st = get_state()
    rec = next(r for r in st.registry.records if r.name_latin and r.id_value)
    with caplog.at_level(logging.DEBUG):
        client.post("/v1/check", json={"name_latin": rec.name_latin, "dob": rec.dob,
                                       "id_value": rec.id_value})  # fmt: skip
        client.post("/v1/names/analyse", json={"name": rec.name_latin})
    text = caplog.text
    secrets = [v for r in st.registry.records for v in (r.name_latin, r.name_ar, r.id_value, r.phone)
               if v and len(v) >= 6 and not is_pattern_placeholder(v)]  # fmt: skip
    assert not [s for s in secrets if s in text]
    assert "registration_check" in text
