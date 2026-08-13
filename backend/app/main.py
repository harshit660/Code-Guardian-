from contextlib import asynccontextmanager
from uuid import uuid4

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.database import Base, engine
from app.rate_limit import RateLimitMiddleware

configure_logging()
log = structlog.get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Development bootstrap. Production deployment should run Alembic migrations before startup.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="CodeGuardian API",
    version="1.0.0",
    description="Repository intelligence, deterministic analysis, and GitHub pull-request feedback.",
    lifespan=lifespan,
    openapi_url=f"{settings.api_prefix}/openapi.json",
    docs_url="/docs",
)
app.add_middleware(CORSMiddleware, allow_origins=settings.origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.add_middleware(RateLimitMiddleware)
app.include_router(api_router, prefix=settings.api_prefix)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    with structlog.contextvars.bound_contextvars(request_id=request_id, method=request.method, path=request.url.path):
        response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/health", tags=["operations"])
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}


@app.exception_handler(Exception)
async def unhandled_exception(_: Request, exc: Exception) -> JSONResponse:
    log.exception("unhandled_exception", error=str(exc))
    return JSONResponse(status_code=500, content={"detail": "An unexpected error occurred"})

