from fastapi import APIRouter
import redis.asyncio as redis
import asyncpg
from app.schemas import market_event as schemas
from app.core.config import settings

router = APIRouter()

@router.get("/health", response_model=schemas.HealthResponse)
async def health():
    redis_status = "ok"
    db_status = "ok"

    # Check Redis
    try:
        r = redis.from_url(settings.REDIS_URL, decode_responses=True)
        await r.ping()
        await r.close()
    except Exception:
        redis_status = "error"

    # Check DB
    try:
        # We need to parse common DB URL to use with asyncpg directly if needed,
        # or just use the engine. For health check, a simple connection is fine.
        # Replacing sync-style driver prefix if present for asyncpg
        url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        conn = await asyncpg.connect(url)
        await conn.fetch("SELECT 1")
        await conn.close()
    except Exception:
        db_status = "error"

    return {"status": "ok", "redis": redis_status, "db": db_status}
