import json
from datetime import date
from uuid import UUID

import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import get_redis
from app.core.db import get_db
from app.crud import market_event as crud
from app.schemas import market_event as schemas
from app.services import provider_service as services

router = APIRouter()


@router.get("/events", response_model=schemas.EventResponse)
async def get_events(
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db),
    r: redis.Redis = Depends(get_redis),
    symbols: str | None = Query(None),
    event_type: str | None = Query(None),
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
    skip: int = 0,
    limit: int = 50,
):
    cache_key = f"events:{request.query_params}"
    cached_events = await r.get(cache_key)
    if cached_events:
        response.headers["X-Cache"] = "HIT"
        return json.loads(cached_events)

    symbol_list = [s.strip() for s in symbols.split(",")] if symbols else None

    events = await crud.get_events(
        db, skip=skip, limit=limit, symbols=symbol_list, event_type=event_type, from_date=from_date, to_date=to_date
    )
    total = await crud.get_events_count(
        db, symbols=symbol_list, event_type=event_type, from_date=from_date, to_date=to_date
    )

    events_data = [schemas.Event.model_validate(e).model_dump() for e in events]

    result = {
        "data": events_data,
        "total": total,
        "limit": limit,
        "offset": skip,
        "has_more": (skip + limit) < total,
    }

    await r.set(cache_key, json.dumps(result, default=str), ex=600)
    response.headers["X-Cache"] = "MISS"

    return result


@router.get("/events/metrics")
async def get_metrics(db: AsyncSession = Depends(get_db)):
    return await crud.get_metrics(db)


@router.get("/events/{event_id}", response_model=schemas.Event)
async def get_event(
    event_id: UUID, response: Response, db: AsyncSession = Depends(get_db), r: redis.Redis = Depends(get_redis)
):
    cache_key = f"event:{event_id}"
    cached_event = await r.get(cache_key)
    if cached_event:
        response.headers["X-Cache"] = "HIT"
        return json.loads(cached_event)

    event = await crud.get_event(db, event_id=event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    response.headers["X-Cache"] = "MISS"
    await r.set(cache_key, schemas.Event.model_validate(event).model_dump_json(), ex=600)
    return event


@router.post("/events/sync", response_model=schemas.SyncResponse)
async def sync_events(
    sync_request: schemas.SyncRequest,
    db: AsyncSession = Depends(get_db),
    r: redis.Redis = Depends(get_redis),
):
    symbols_to_sync, symbols_skipped = await services.get_symbols_to_sync(db, sync_request.symbols, sync_request.force)

    created_a, updated_a = await services.sync_provider_a(db, symbols_to_sync)
    created_b, updated_b = await services.sync_provider_b(db, symbols_to_sync)

    await services.update_sync_log(db, symbols_to_sync)

    for symbol in symbols_to_sync:
        await r.set(f"last_sync:{symbol}", "1", ex=600)

    return {
        "status": "completed",
        "symbols_synced": symbols_to_sync,
        "symbols_skipped": symbols_skipped,
        "events_created": created_a + created_b,
        "events_updated": updated_a + updated_b,
        "errors": [],
    }
