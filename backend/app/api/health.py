"""Health check endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from app.core.database import get_db
from app.core.redis import get_redis
from app.schemas.response import ResponseModel

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=ResponseModel)
async def health_check():
    """Basic health check endpoint."""
    return ResponseModel(
        code=200,
        message="OK",
        data={"status": "healthy"}
    )


@router.get("/health/db", response_model=ResponseModel)
async def health_check_db(db: AsyncSession = Depends(get_db)):
    """Health check with database connectivity."""
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return ResponseModel(
        code=200,
        message="OK",
        data={
            "status": "healthy",
            "database": db_status
        }
    )


@router.get("/health/redis", response_model=ResponseModel)
async def health_check_redis():
    """Health check with Redis connectivity."""
    try:
        redis_client = await get_redis()
        await redis_client.ping()
        redis_status = "connected"
    except Exception as e:
        redis_status = f"error: {str(e)}"
    
    return ResponseModel(
        code=200,
        message="OK",
        data={
            "status": "healthy",
            "redis": redis_status
        }
    )


@router.get("/health/full", response_model=ResponseModel)
async def health_check_full(db: AsyncSession = Depends(get_db)):
    """Full health check with all services."""
    health_data = {"status": "healthy"}
    
    # Check database
    try:
        await db.execute(text("SELECT 1"))
        health_data["database"] = "connected"
    except Exception as e:
        health_data["database"] = f"error: {str(e)}"
        health_data["status"] = "degraded"
    
    # Check Redis
    try:
        redis_client = await get_redis()
        await redis_client.ping()
        health_data["redis"] = "connected"
    except Exception as e:
        health_data["redis"] = f"error: {str(e)}"
        health_data["status"] = "degraded"
    
    return ResponseModel(
        code=200,
        message="OK",
        data=health_data
    )
