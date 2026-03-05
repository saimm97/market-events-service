import contextlib
from datetime import datetime

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.crud import market_event as crud

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def format_iso_datetime(dt: datetime) -> str:
    if not dt:
        return "N/A"
    return dt.strftime("%b %d, %Y %H:%M UTC")


@router.get("/")
async def dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db),
    symbol: str | None = None,
    event_type: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
):
    metrics = await crud.get_metrics(db)

    for _symbol, info in metrics["symbols"].items():
        info["last_synced_at"] = format_iso_datetime(info["last_synced_at"])

    # Parse dates if provided
    f_date = None
    if from_date:
        with contextlib.suppress(ValueError):
            f_date = datetime.strptime(from_date, "%Y-%m-%d").date()

    t_date = None
    if to_date:
        with contextlib.suppress(ValueError):
            t_date = datetime.strptime(to_date, "%Y-%m-%d").date()

    # Use filtering logic
    symbol_list = [symbol.strip()] if symbol else None
    events = await crud.get_events(
        db, limit=50, symbols=symbol_list, event_type=event_type, from_date=f_date, to_date=t_date
    )

    formatted_events = []
    for event in events:
        event_dict = {
            "symbol": event.symbol,
            "event_type": event.event_type,
            "event_date": format_iso_datetime(event.event_date),
            "title": event.title,
            "source": event.source,
            "created_at": format_iso_datetime(event.created_at),
        }
        formatted_events.append(event_dict)

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "metrics": metrics,
            "events": formatted_events,
            "filters": {
                "symbol": symbol or "",
                "event_type": event_type or "",
                "from_date": from_date or "",
                "to_date": to_date or "",
            },
        },
    )
