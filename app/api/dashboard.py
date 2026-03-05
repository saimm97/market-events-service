from datetime import datetime
from fastapi import APIRouter, Request, Depends
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
async def dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    # Direct service calls instead of internal HTTP for better performance/reliability
    metrics = await crud.get_metrics(db)
    
    # Format dates in metrics
    for symbol, info in metrics["symbols"].items():
        info["last_synced_at"] = format_iso_datetime(info["last_synced_at"])

    # Fetch latest 50 events
    events = await crud.get_events(db, limit=50)
    
    # Format dates in events
    formatted_events = []
    for event in events:
        event_dict = {
            "symbol": event.symbol,
            "event_type": event.event_type,
            "event_date": format_iso_datetime(event.event_date),
            "title": event.title,
            "source": event.source,
            "created_at": format_iso_datetime(event.created_at)
        }
        formatted_events.append(event_dict)

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "metrics": metrics,
        "events": formatted_events
    })
