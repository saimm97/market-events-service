import pytest_asyncio
import redis.asyncio as redis
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.cache import get_redis
from app.core.config import settings
from app.core.db import get_db
from app.main import app
from app.models.market_event import Base

# Use the same DB for now but clean up
TEST_DATABASE_URL = settings.DATABASE_URL.replace("asyncpg", "asyncpg")


@pytest_asyncio.fixture(scope="function")
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)
    async with Session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def redis_client():
    client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    yield client
    await client.flushdb()
    await client.close()


@pytest_asyncio.fixture(scope="function")
async def client(db_session, redis_client):
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_redis] = lambda: redis_client

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
