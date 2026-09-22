import uuid
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy import text
import redis.asyncio as aioredis

from app.core.config import settings
from app.db.session import engine
from app.api.v1.auth import router as auth_router
from app.api.v1.bots import router as bots_router
from app.api.v1.chat import router as chat_router
from app.api.v1.widget import router as widget_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("embediq")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Verify database and redis connection
    logger.info("Initializing EmbedIQ backend application...")
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("PostgreSQL database connection pool established.")
    except Exception as e:
        logger.warning(f"Database connection check during startup failed (will retry on requests): {e}")

    try:
        r = aioredis.from_url(settings.REDIS_URL)
        await r.ping()
        await r.aclose()
        logger.info("Redis connection established.")
    except Exception as e:
        logger.warning(f"Redis connection check during startup failed: {e}")

    yield

    # Shutdown: Close engine
    logger.info("Shutting down EmbedIQ backend application...")
    await engine.dispose()
    logger.info("Database connection pool closed.")


app = FastAPI(
    title=settings.APP_NAME,
    description="Embeddable Website-Specific RAG Chatbot Platform API",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,

    # EmbedIQ's widget is intentionally embeddable on third-party domains.
    # Authentication is performed using explicit Bearer tokens rather than
    # cross-origin cookies, so credentialed CORS must remain disabled.
    allow_origins=["*"],
    allow_credentials=False,

    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting (PRD Section 11.3)
from app.core.rate_limit import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware)


# Standard Error Envelope Helper
def create_error_response(
    code: str,
    message: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    request_id: str = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "request_id": request_id or str(uuid.uuid4()),
            }
        },
    )


# Global Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    error_msg = "; ".join([f"{e.get('loc', [])}: {e.get('msg')}" for e in errors])
    return create_error_response(
        code="VALIDATION_ERROR",
        message=f"Request validation failed: {error_msg}",
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return create_error_response(
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected server error occurred.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


from app.api.v1.analytics import router as analytics_router

# Include API routers
app.include_router(auth_router, prefix="/api")
app.include_router(bots_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")

# Widget endpoints: allow all origins (public, no credentials)
from fastapi.middleware.cors import CORSMiddleware as _CORSMiddleware  # noqa: E402
app.include_router(widget_router, prefix="/api")


# Health Check Endpoints
@app.get("/api/health", tags=["System"])
async def health_check() -> Dict[str, Any]:
    db_status = "ok"
    redis_status = "ok"

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    try:
        r = aioredis.from_url(settings.REDIS_URL)
        await r.ping()
        await r.aclose()
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"

    is_healthy = db_status == "ok" and redis_status == "ok"

    return {
        "status": "healthy" if is_healthy else "degraded",
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "version": "2.0.0",
        "services": {
            "database": db_status,
            "redis": redis_status,
        },
    }


@app.get("/", tags=["System"])
async def root() -> Dict[str, str]:
    return {
        "name": settings.APP_NAME,
        "version": "2.0.0",
        "status": "online",
        "docs": "/docs",
    }
