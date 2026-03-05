import redis.asyncio as redis
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import get_redis
from app.core.db import get_db
from app.schemas import market_event as schemas

router = APIRouter()


@router.get("/health", response_model=schemas.HealthResponse)
async def health(db: AsyncSession = Depends(get_db), r: redis.Redis = Depends(get_redis)):
    redis_status = "ok"
    db_status = "ok"

    try:
        await r.ping()
    except Exception:
        redis_status = "error"

    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    return {"status": "ok", "redis": redis_status, "db": db_status}
