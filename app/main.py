from fastapi import FastAPI
from app.api import events, health
from app.core.db import engine
from app.models import market_event
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(market_event.Base.metadata.create_all)

# Include routers
app.include_router(health.router, prefix=settings.API_V1_STR, tags=["health"])
app.include_router(events.router, prefix=settings.API_V1_STR, tags=["events"])