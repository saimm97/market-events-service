from fastapi import APIRouter, Depends
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.schemas import market_event as schemas
from app.core.db import get_db
from app.core.cache import get_redis

router = APIRouter()

@router.get("/health", response_model=schemas.HealthResponse)
async def health(
    db: AsyncSession = Depends(get_db),
    r: redis.Redis = Depends(get_redis)
):
    redis_status = "ok"
    db_status = "ok"

    # Check Redis
    try:
        await r.ping()
    except Exception:
        redis_status = "error"

    # Check DB
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    return {"status": "ok", "redis": redis_status, "db": db_status}
