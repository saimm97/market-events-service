from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import market_event as models
from app.schemas import market_event as schemas


def _apply_event_filters(
    query: Any,
    symbols: list[str] | None = None,
    event_type: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
):
    if symbols:
        query = query.filter(models.Event.symbol.in_(symbols))
    if event_type:
        query = query.filter(models.Event.event_type == event_type)
    if from_date:
        query = query.filter(models.Event.event_date >= from_date)
    if to_date:
        query = query.filter(models.Event.event_date <= to_date)
    return query


async def get_event(db: AsyncSession, event_id: UUID):
    result = await db.execute(select(models.Event).filter(models.Event.id == event_id))
    return result.scalars().first()


async def get_events(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    symbols: list[str] | None = None,
    event_type: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
):
    query = select(models.Event)
    query = _apply_event_filters(query, symbols, event_type, from_date, to_date)
    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()


async def get_events_count(
    db: AsyncSession,
    symbols: list[str] | None = None,
    event_type: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
):
    query = select(func.count()).select_from(models.Event)
    query = _apply_event_filters(query, symbols, event_type, from_date, to_date)
    result = await db.execute(query)
    return result.scalar()


async def get_event_by_unique_constraint(db: AsyncSession, event: schemas.EventCreate):
    result = await db.execute(
        select(models.Event).filter(
            models.Event.symbol == event.symbol,
            models.Event.event_type == event.event_type,
            models.Event.event_date == event.event_date,
        )
    )
    return result.scalars().first()


async def create_or_update_event(db: AsyncSession, event: schemas.EventCreate):
    try:
        db_event = models.Event(**event.model_dump())
        db.add(db_event)
        await db.commit()
        await db.refresh(db_event)
        return db_event, True
    except IntegrityError:
        await db.rollback()
        db_event = await get_event_by_unique_constraint(db, event)
        if db_event:
            for key, value in event.model_dump().items():
                setattr(db_event, key, value)
            await db.commit()
            await db.refresh(db_event)
            return db_event, False
        return None, False
