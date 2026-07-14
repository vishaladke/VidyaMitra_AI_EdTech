"""FastAPI application entry point.

Mounts all routers, configures CORS, and sets up lifespan events.
Super Admin router is mounted at /{SUPERADMIN_URL_PATH}/api/...
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, health, students, teachers, parents, admin, superadmin, ai, syllabus

logging.basicConfig(
    level=logging.INFO if settings.ENVIRONMENT == "local" else logging.WARNING,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info(f"🚀 VidyaMitra Backend starting (env={settings.ENVIRONMENT})")
    logger.info(f"   OTP provider: {settings.OTP_PROVIDER}")
    logger.info(f"   Payment provider: {settings.PAYMENT_PROVIDER}")
    logger.info(f"   AI model: {settings.AI_DEFAULT_MODEL}")
    if settings.ENVIRONMENT == "local":
        logger.info(f"   📍 Super Admin URL: /{settings.SUPERADMIN_URL_PATH}/api/...")
        logger.info(f"   🔑 Dev OTP code: {settings.DEV_OTP_CODE}")
    yield
    logger.info("VidyaMitra Backend shutting down")


app = FastAPI(
    title="VidyaMitra AI EdTech Platform",
    description="AI-native EdTech platform for Marathi-medium students in Maharashtra",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT == "local" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "local" else None,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount routers ─────────────────────────────────────────

# Public + authenticated routes
app.include_router(health.router)
app.include_router(auth.router)

# Role-specific routes (RBAC enforced per-endpoint)
app.include_router(students.router)
app.include_router(teachers.router)
app.include_router(parents.router)
app.include_router(admin.router)

# Feature routes (RBAC enforced per-endpoint inside each router)
app.include_router(ai.router)
app.include_router(syllabus.router)

# Super Admin — mounted at /{SUPERADMIN_URL_PATH}/api/...
# This path is NOT linked from any public navigation
app.include_router(
    superadmin.router,
    prefix=f"/{settings.SUPERADMIN_URL_PATH}/api",
)
