"""FastAPI application entrypoint for AI Penfight."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ai.clients.llm_client import get_llm_client
from backend.app.config import settings
from backend.app.routers.analysis import router as analysis_router
from backend.app.schemas import HealthResponse

logging.basicConfig(
    level=settings.LOG_LEVEL.upper(),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ai_penfight.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = get_llm_client()
    logger.info(
        "AI Penfight Backend initialized. Provider: %s, Available: %s",
        client.get_provider_name(),
        client.is_available(),
    )
    yield
    logger.info("AI Penfight Backend shutting down.")


app = FastAPI(
    title="AI Penfight API",
    description="Intelligent analysis, pattern detection, and adaptive feedback engine for debate practice.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Ensure standard JSON error shape on Pydantic request validation failure."""
    first_error = exc.errors()[0] if exc.errors() else {}
    msg = first_error.get("msg", "Invalid request payload.")
    field = ".".join(str(loc) for loc in first_error.get("loc", []))
    if field:
        msg = f"Field '{field}': {msg}"

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": msg,
            },
        },
    )


# Include Routers
app.include_router(analysis_router)


@app.get("/api/v1/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Liveness and AI provider availability check."""
    client = get_llm_client()
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        ai_provider=client.get_provider_name(),
        ai_available=client.is_available(),
    )


@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "AI Penfight API",
        "status": "online",
        "docs_url": "/docs",
    }
