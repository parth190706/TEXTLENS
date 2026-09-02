"""
TextLens — FastAPI application entry point.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import init_db
from app.api.documents import router as documents_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("TextLens starting up...")
    await init_db()
    logger.info("Database initialized")
    yield
    logger.info("TextLens shutting down")


app = FastAPI(
    title="TextLens API",
    description="Intelligent document analysis — structured, traceable, explainable.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ── CORS ──────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Exception handlers ────────────────────────────────────────────

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred.", "code": "INTERNAL_ERROR"},
    )

# ── Routers ───────────────────────────────────────────────────────

app.include_router(documents_router)


# ── Health ────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "TextLens API"}
