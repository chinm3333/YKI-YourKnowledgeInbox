from contextlib import asynccontextmanager
import logging
import time
import uuid
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from logging_config import setup_logging
from routers import ingest, items, query
from services.errors import AppError
from services.store import init_db
setup_logging()
logger = logging.getLogger("knowledge_inbox")

@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    logger.info("API started")
    yield

app = FastAPI(title="AI Knowledge Inbox",version="0.1.0",description="Single-user notes + URL inbox with local RAG.",lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router)
app.include_router(items.router)
app.include_router(query.router)

@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    started = time.perf_counter()
    response = await call_next(request)
    latency_ms = round((time.perf_counter() - started) * 1000, 1)
    logger.info(
        "request",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "latency_ms": latency_ms,
        },
    )
    response.headers["x-request-id"] = request_id
    return response

def _friendly_validation(exc: RequestValidationError) -> str:
    parts = []
    for err in exc.errors():
        loc = ".".join(str(x) for x in err.get("loc", []) if x != "body")
        msg = err.get("msg", "Invalid value")
        if msg.startswith("Value error, "):
            msg = msg[len("Value error, "):]
        parts.append(f"{loc}: {msg}" if loc else msg)
    return "; ".join(parts) or "Invalid request"

@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.code, "detail": exc.detail},
    )

@app.exception_handler(HTTPException)
async def http_handler(_: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "request_failed", "detail": exc.detail},
    )

@app.exception_handler(RequestValidationError)
async def validation_handler(_: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"error": "validation_error", "detail": _friendly_validation(exc)},
    )

@app.exception_handler(Exception)
async def unhandled_handler(_: Request, exc: Exception):
    if isinstance(exc, AppError):
        return await app_error_handler(_, exc)
    if isinstance(exc, HTTPException):
        return await http_handler(_, exc)
    logger.exception("Unhandled error")
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "detail": "Unexpected server error"},
    )

@app.get("/health")
def health():
    return {"status": "ok"}
