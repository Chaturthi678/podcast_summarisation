"""
Podly AI — FastAPI Application Entry Point
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import create_tables
from app.api.podcasts import router as podcasts_router
from app.api.jobs import router as jobs_router

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("Starting Podly AI backend…")
    create_tables()
    logger.info(f"Upload dir:  {settings.UPLOAD_DIR}")
    logger.info(f"Output dir:  {settings.OUTPUT_DIR}")
    logger.info(f"Whisper model: {settings.WHISPER_MODEL} on {settings.WHISPER_DEVICE}")
    logger.info(f"Summarizer:    {settings.SUMMARIZER_MODEL}")
    logger.info("Podly AI backend ready ✓")
    yield


# Create FastAPI app
app = FastAPI(
    title="Podly AI",
    description="AI-powered podcast summariser and chapter generator",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(podcasts_router)
app.include_router(jobs_router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "Podly AI"}
