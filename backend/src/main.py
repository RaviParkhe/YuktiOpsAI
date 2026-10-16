import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from src.api.routes_ads import router as ads_router
from src.api.routes_auth import router as auth_router
from src.api.routes_credits import router as credits_router
from src.api.routes_github import router as github_router
from src.api.routes_projects import router as projects_router
from src.api.routes_research import router as research_router
from src.api.routes_solutions import router as solutions_router
from src.api.routes_telegram import router as telegram_router
from src.auth import get_auth_status
from src.config import get_settings
from src.db.session import engine, init_db

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Safely initialise database schema on startup
    try:
        await init_db()
        logger.info("Application startup: database initialised successfully.")
    except Exception as exc:
        logger.warning(f"Application startup: database init warning: {exc}")
    yield
    try:
        await engine.dispose()
        logger.info("Application shutdown: database engine disposed.")
    except Exception as exc:
        logger.warning(f"Application shutdown: engine disposal warning: {exc}")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1/auth")
app.include_router(projects_router, prefix="/api/v1/projects")
app.include_router(credits_router, prefix="/api/v1/credits")
app.include_router(ads_router, prefix="/api/v1/ads")
app.include_router(solutions_router, prefix="/api/v1/solutions")
app.include_router(research_router, prefix="/api/v1/research")
app.include_router(github_router, prefix="/api/v1/github")
app.include_router(telegram_router, prefix="/api/v1/telegram")


@app.get("/health", tags=["Health"])
async def health_check():
    """Liveness probe — returns service info without verifying external dependencies."""
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/ready", tags=["Health"])
async def readiness_check(response: Response):
    """Readiness probe — verifies database connectivity and reports authentication mode."""
    db_ok = False
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            db_ok = result.scalar() == 1
    except Exception as e:
        logger.warning(f"Readiness check DB error: {e}")
        db_ok = False

    auth_info = get_auth_status()

    if not db_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "not_ready",
            "database": "disconnected",
            "auth": auth_info,
        }

    return {
        "status": "ready",
        "database": "connected",
        "auth": auth_info,
    }
