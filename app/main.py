from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api import dashboard, events, health
from app.core.config import settings
from app.core.db import engine
from app.models import market_event

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(market_event.Base.metadata.create_all)


# Include routers
app.include_router(dashboard.router, tags=["dashboard"])
app.include_router(health.router, prefix=settings.API_V1_STR, tags=["health"])
app.include_router(events.router, prefix=settings.API_V1_STR, tags=["events"])
