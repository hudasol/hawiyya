"""FastAPI service, versioned under /v1. Errors use application/problem+json.

Server logs carry only fixed event names, counts and record ids: request bodies (names and
identifiers) are never logged.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import FastAPI, Path, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException

from hawiyya.api import batch, content, service
from hawiyya.api.schemas import ActionInput, CheckOut, NameInput, RegistrationInput, ScoreInput
from hawiyya.contract.models import Costs
from hawiyya.workflow.queue import IllegalTransition

MAX_BODY_BYTES = 16 * 1024
PROBLEM = "application/problem+json"

app = FastAPI(
    title="Hawiyya API",
    version="0.5.0",
    description="Decision support on synthetic patient records. Advisory only; all data synthetic.",
)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173",
                   "http://127.0.0.1:5173", "http://localhost:4173"], allow_methods=["*"],
                   allow_headers=["*"])  # fmt: skip


def problem(status: int, title: str, detail: str, type_: str = "about:blank") -> JSONResponse:
    return JSONResponse(
        {"type": type_, "title": title, "status": status, "detail": detail},
        status_code=status, media_type=PROBLEM,
    )


@app.middleware("http")
async def limit_body(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    length = request.headers.get("content-length")
    if length is not None and int(length) > MAX_BODY_BYTES:
        return problem(413, "Request too large", f"Bodies are limited to {MAX_BODY_BYTES} bytes.")
    return await call_next(request)


@app.exception_handler(RequestValidationError)
async def on_validation(_: Request, exc: RequestValidationError) -> JSONResponse:
    fields = sorted({".".join(str(p) for p in e.get("loc", [])[1:]) for e in exc.errors()})
    return problem(422, "Invalid request", "Invalid fields: " + ", ".join(fields))


@app.exception_handler(StarletteHTTPException)
async def on_http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    return problem(exc.status_code, "Request failed", str(exc.detail))


@app.exception_handler(Exception)
async def on_error(_: Request, exc: Exception) -> JSONResponse:
    return problem(500, "Internal error", type(exc).__name__)


@app.get("/v1/health")
def health() -> dict[str, Any]:
    return service.health()


@app.get("/v1/registry/summary")
def registry_summary() -> dict[str, Any]:
    return service.registry_summary()


@app.post("/v1/check", response_model=CheckOut)
def check(body: RegistrationInput) -> CheckOut:
    return service.check(body)


@app.post("/v1/score")
def score(body: ScoreInput) -> dict[str, Any]:
    return service.score(body)


@app.post("/v1/names/analyse")
def names_analyse(body: NameInput) -> dict[str, Any]:
    return service.names_analyse(body)


def _env(payload: dict[str, Any]) -> dict[str, Any]:
    return service._envelope(payload)


@app.get("/v1/review/queue")
def review_queue(limit: int = Query(100, ge=1, le=500)) -> dict[str, Any]:
    return _env(batch.review_queue(limit))


@app.get("/v1/review/{case_id}")
def review_case(case_id: str = Path(pattern=r"^C[0-9A-F]{10}$")) -> dict[str, Any]:
    out = batch.review_case(case_id)
    if out is None:
        raise StarletteHTTPException(404, "No such review case.")
    return _env(out)


@app.post("/v1/review/{case_id}/action")
def review_action(body: ActionInput,
                  case_id: str = Path(pattern=r"^C[0-9A-F]{10}$")) -> dict[str, Any]:
    if batch.review_case(case_id) is None:
        raise StarletteHTTPException(404, "No such review case.")
    try:
        return _env(batch.review_action(case_id, body.action))
    except IllegalTransition as exc:
        raise StarletteHTTPException(409, str(exc)) from exc


@app.get("/v1/clusters")
def clusters(limit: int = Query(100, ge=1, le=500)) -> dict[str, Any]:
    return _env(batch.clusters(limit))


@app.get("/v1/clusters/{cluster_id}")
def cluster_detail(cluster_id: str = Path(pattern=r"^K\d{4}$")) -> dict[str, Any]:
    out = batch.cluster_detail(cluster_id)
    if out is None:
        raise StarletteHTTPException(404, "No such cluster.")
    return _env(out)


@app.get("/v1/export/fhir/{cluster_id}")
def export_fhir(cluster_id: str = Path(pattern=r"^K\d{4}$")) -> dict[str, Any]:
    out = batch.cluster_detail(cluster_id)
    if out is None:
        raise StarletteHTTPException(404, "No such cluster.")
    bundle: dict[str, Any] = out["fhir_bundle"]
    return bundle


@app.get("/v1/placeholders")
def placeholders() -> dict[str, Any]:
    return _env(batch.placeholders())


@app.get("/v1/thresholds/curve")
def thresholds_curve() -> dict[str, Any]:
    return _env(batch.threshold_curve())


@app.post("/v1/thresholds/simulate")
def thresholds_simulate(body: Costs) -> dict[str, Any]:
    return _env(batch.simulate_costs(body))


@app.get("/v1/fairness")
def fairness() -> dict[str, Any]:
    return _env(content.fairness())


@app.get("/v1/experiments")
def experiments() -> dict[str, Any]:
    return _env(content.experiments())


@app.get("/v1/method")
def method() -> dict[str, Any]:
    return _env(content.method())


@app.get("/v1/claims")
def claims() -> dict[str, Any]:
    return _env(content.claims())


@app.get("/v1/provenance")
def provenance() -> dict[str, Any]:
    return _env(content.provenance())


@app.get("/v1/audit")
def audit(limit: int = Query(200, ge=1, le=1000)) -> dict[str, Any]:
    return _env(batch.audit(limit))
