from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud import market_event as crud
from app.models.market_event import EventSyncLog
from app.schemas import market_event as schemas
from providers.provider_a import ProviderA
from providers.provider_b import ProviderB


def format_event_title(symbol: str, event_type: str, event_datetime: datetime):
    """
    Returns a normalized title: always 'SYMBOL event_type YYYY-MM-DD HH:MM:SS'
    If time is missing, use 00:00:00
    """
    if not event_datetime:
        event_datetime = datetime.now(UTC)
    return f"{symbol.upper()} {event_type.upper()} {event_datetime.strftime('%Y-%m-%d %H:%M:%S')}"


async def sync_provider_a(db: AsyncSession, symbols: list[str]):
    """
    Fetches events from Provider A, normalizes them, and stores them in the database.
    """
    created_count = 0
    updated_count = 0
    async with ProviderA(api_key=settings.PROVIDER_A_API_KEY) as provider:
        events = await provider.fetch_events(symbols)
        for event in events:
            normalized_event = normalize_provider_a_event(event)
            _, created = await crud.create_or_update_event(db, schemas.EventCreate(**normalized_event))
            if created:
                created_count += 1
            else:
                updated_count += 1
    return created_count, updated_count


def normalize_provider_a_event(event: dict[str, Any]) -> dict[str, Any]:
    """
    Normalizes an event from Provider A to the unified data model.
    """
    date_str = event.get("date")
    time_str = event.get("time")

    if not time_str or str(time_str).lower() == "none":
        time_str = "00:00:00"

    event_datetime_str = f"{date_str}T{time_str}"

    try:
        event_date = datetime.fromisoformat(event_datetime_str)
    except ValueError:
        event_date = datetime.now(UTC)

    normalized_title = format_event_title(event["ticker"], event["type"], event_date)
    return {
        "symbol": event["ticker"],
        "event_type": event["type"],
        "event_date": datetime.fromisoformat(event_datetime_str),
        "title": normalized_title,
        "details": event["details"],
        "source": "provider_a",
        "provider_event_id": event["event_id"],
    }


async def sync_provider_b(db: AsyncSession, symbols: list[str]):
    """
    Fetches events from Provider B, normalizes them, and stores them in the database.
    """
    created_count = 0
    updated_count = 0
    async with ProviderB(api_key=settings.PROVIDER_B_API_KEY) as provider:
        result = await provider.fetch_events(symbols)
        events = result["events"]
        for event in events:
            normalized_event = normalize_provider_b_event(event)
            _, created = await crud.create_or_update_event(db, schemas.EventCreate(**normalized_event))
            if created:
                created_count += 1
            else:
                updated_count += 1

        while result["pagination"]["has_next"]:
            result = await provider.fetch_events(symbols, cursor=result["pagination"]["next_cursor"])
            events = result["events"]
            for event in events:
                normalized_event = normalize_provider_b_event(event)
                _, created = await crud.create_or_update_event(db, schemas.EventCreate(**normalized_event))
                if created:
                    created_count += 1
                else:
                    updated_count += 1
    return created_count, updated_count


def normalize_provider_b_event(event: dict[str, Any]) -> dict[str, Any]:
    """
    Normalizes an event from Provider B to the unified data model.
    """
    event_type_mapping = {
        "earnings_release": "earnings",
        "dividend_payment": "dividend",
        "stock_split": "split",
        "economic_indicator": "economic",
    }

    evt_date = datetime.fromisoformat(event["event"]["scheduled_at"].replace("Z", "+00:00"))
    evt_type = event_type_mapping.get(event["event"]["category"], "unknown")
    normalized_title = format_event_title(event["instrument"]["symbol"], evt_type, evt_date)

    return {
        "symbol": event["instrument"]["symbol"],
        "event_type": event_type_mapping.get(event["event"]["category"], "unknown"),
        "event_date": datetime.fromisoformat(event["event"]["scheduled_at"].replace("Z", "+00:00")),
        "title": normalized_title,
        "details": event["event"],
        "source": "provider_b",
        "provider_event_id": event["id"],
    }


async def get_symbols_to_sync(db: AsyncSession, symbols: list[str], force: bool):
    symbols_to_sync = []
    symbols_skipped = []

    if force:
        symbols_to_sync = symbols
    else:
        one_hour_ago = datetime.now(UTC) - timedelta(hours=1)
        for symbol in symbols:
            result = await db.execute(select(EventSyncLog).filter(EventSyncLog.symbol == symbol))
            log = result.scalars().first()
            if log and log.last_synced_at > one_hour_ago:
                symbols_skipped.append(symbol)
            else:
                symbols_to_sync.append(symbol)

    return symbols_to_sync, symbols_skipped


async def update_sync_log(db: AsyncSession, symbols: list[str]):
    now = datetime.now(UTC)
    for symbol in symbols:
        result = await db.execute(select(EventSyncLog).filter(EventSyncLog.symbol == symbol))
        log = result.scalars().first()
        if log:
            log.last_synced_at = now
        else:
            db.add(EventSyncLog(symbol=symbol, last_synced_at=now))
    await db.commit()
