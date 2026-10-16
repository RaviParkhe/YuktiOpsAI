import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.api import api_router
from src.config import get_settings
from src.db.session import init_db
from src.schemas.common import APIResponse, ErrorDetail, ErrorResponse

# Configure structured logging
settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("yuktiops.agent")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup and shutdown routines."""
    logger.info("Initializing database schemas...")
    await init_db()
    logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} initialized and ready.")
    yield
    logger.info("Shutting down agent service...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Production-minded AI agent service for YuktiOps. "
        "Deterministic orchestrator with specialized logical agents for GitHub PR analysis, "
        "triage, Telegram escalation, and human-approved fix proposals."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Enable CORS for Next.js / React dashboards and external services.
# ALLOWED_ORIGINS is loaded from the .env file (e.g. http://localhost:3000,https://app.example.com).
# allow_credentials must remain False when allow_origins contains "*" (browser CORS spec).
# Set allow_credentials=True only when ALLOWED_ORIGINS lists explicit origins AND you use session/cookie auth.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Hub-Signature-256", "X-GitHub-Event", "X-GitHub-Delivery"],
)


# Consistent error handling: HTTPException
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict):
        code = detail.get("code", "HTTP_ERROR")
        msg = detail.get("message", "An error occurred")
    else:
        code = "HTTP_ERROR"
        msg = str(detail)

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            success=False,
            error=ErrorDetail(code=code, message=msg),
        ).model_dump(),
    )


# Consistent error handling: RequestValidationError
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    first_err = exc.errors()[0] if exc.errors() else {}
    loc = " -> ".join([str(x) for x in first_err.get("loc", [])])
    msg = first_err.get("msg", "Invalid request parameter")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            success=False,
            error=ErrorDetail(
                code="VALIDATION_ERROR",
                message=msg,
                location=loc,
            ),
        ).model_dump(),
    )


@app.get("/health", response_model=APIResponse[dict], tags=["System"])
async def health_check():
    """Health check endpoint for container orchestrators and monitoring."""
    return APIResponse(
        success=True,
        message="YuktiOps Agent Service is healthy",
        data={
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT.value,
        },
    )


# Mount API V1 Routes
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
