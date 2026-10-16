"""FastAPI service, versioned under /v1. Errors use application/problem+json.

Server logs carry only fixed event names, counts and record ids: request bodies (names and
identifiers) are never logged.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException

from hawiyya.api import service
from hawiyya.api.schemas import CheckOut, NameInput, RegistrationInput, ScoreInput

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
