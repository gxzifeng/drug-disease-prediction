"""FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.database import init_db, AsyncSessionLocal
from app.core.redis import close_redis
from app.core.exceptions import AppException
from app.api import health, auth, users, datasets, drugs, diseases, graphs, embeddings, experiments, predictions, models
from app.schemas.response import ErrorResponse, ErrorDetail
from app.services.auth import AuthService

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    await init_db()
    logger.info("Database initialized")
    
    # Initialize default roles and superuser
    async with AsyncSessionLocal() as session:
        try:
            auth_service = AuthService(session)
            await auth_service.init_default_roles()
            superuser = await auth_service.init_superuser()
            await session.commit()
            if superuser:
                logger.info(f"Created default superuser: {superuser.username}")
            logger.info("Default roles initialized")
        except Exception as e:
            await session.rollback()
            logger.warning(f"Could not initialize defaults: {e}")
    
    yield
    
    # Shutdown
    await close_redis()
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="药物-疾病关联预测系统 API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handlers
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handle custom application exceptions."""
    logger.warning(f"AppException: {exc.error_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            code=exc.status_code,
            message=exc.detail if isinstance(exc.detail, str) else "An error occurred",
            errors=[{"code": exc.error_code}] if exc.error_code else None
        ).model_dump()
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle FastAPI HTTPExceptions."""
    logger.warning(f"HTTPException: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            code=exc.status_code,
            message=exc.detail if isinstance(exc.detail, str) else "An error occurred"
        ).model_dump()
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    logger.warning(f"ValidationError: {exc.errors()}")
    errors = [
        ErrorDetail(
            field=".".join(map(str, error.get("loc", []))),
            message=error.get("msg", "Validation error")
        )
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            code=422,
            message="Validation error",
            errors=errors
        ).model_dump()
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    # Log the full exception for debugging
    logger.exception(f"Unhandled exception: {exc}")
    
    # In production, return a generic message without exposing internals
    if settings.DEBUG:
        message = f"Internal server error: {str(exc)}"
    else:
        message = "An unexpected error occurred. Please try again later."
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            code=500,
            message=message
        ).model_dump()
    )


# Include routers
app.include_router(health.router, prefix=settings.API_PREFIX)
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(users.router, prefix=settings.API_PREFIX)
app.include_router(datasets.router, prefix=settings.API_PREFIX)
app.include_router(drugs.router, prefix=settings.API_PREFIX)
app.include_router(diseases.router, prefix=settings.API_PREFIX)
app.include_router(graphs.router, prefix=settings.API_PREFIX)
app.include_router(embeddings.router, prefix=settings.API_PREFIX)
app.include_router(experiments.router, prefix=settings.API_PREFIX)
app.include_router(models.router, prefix=settings.API_PREFIX)
app.include_router(predictions.router, prefix=settings.API_PREFIX)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": f"{settings.API_PREFIX}/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
