from datetime import datetime
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.market_event import Event


@pytest.mark.asyncio
async def test_get_events_empty(client: AsyncClient):
    response = await client.get("/api/v1/events")
    assert response.status_code == 200
    data = response.json()
    assert data["data"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_create_and_get_event(db_session: AsyncSession, client: AsyncClient):
    # Setup test data
    event_id = uuid4()
    db_event = Event(
        id=event_id,
        symbol="AAPL",
        event_type="earnings",
        event_date=datetime(2026, 3, 5),
        title="Q1 Earnings",
        details={"eps": 1.5},
        source="provider_a",
        provider_event_id="test_id_1",
    )
    db_session.add(db_event)
    await db_session.commit()

    # Test API
    response = await client.get("/api/v1/events")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["data"][0]["symbol"] == "AAPL"
    assert data["data"][0]["id"] == str(event_id)


@pytest.mark.asyncio
async def test_get_event_by_id(db_session: AsyncSession, client: AsyncClient):
    # Setup
    event_id = uuid4()
    db_event = Event(
        id=event_id,
        symbol="MSFT",
        event_type="dividend",
        event_date=datetime(2026, 3, 5),
        title="MSFT Dividend",
        details={},
        source="provider_a",
        provider_event_id="test_msft_1",
    )
    db_session.add(db_event)
    await db_session.commit()

    # Test
    response = await client.get(f"/api/v1/events/{event_id}")
    assert response.status_code == 200
    assert response.json()["symbol"] == "MSFT"


@pytest.mark.asyncio
async def test_get_event_not_found(client: AsyncClient):
    response = await client.get(f"/api/v1/events/{uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_sync_events_endpoint(client: AsyncClient, mocker):
    # Mock the provider sync calls to avoid external network access
    mocker.patch("app.services.provider_service.sync_provider_a", return_value=(1, 0))
    mocker.patch("app.services.provider_service.sync_provider_b", return_value=(0, 1))

    payload = {"symbols": ["AAPL", "GOOGL"], "force": True}
    response = await client.post("/api/v1/events/sync", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["events_created"] == 1
    assert data["events_created"] == 1
    assert data["events_updated"] == 1


@pytest.mark.asyncio
async def test_get_metrics(db_session: AsyncSession, client: AsyncClient):
    # Setup
    event = Event(
        symbol="TSLA",
        event_type="split",
        event_date=datetime(2026, 3, 5),
        title="TSLA Split",
        details={},
        source="provider_a",
        provider_event_id="test_tsla_1",
    )
    db_session.add(event)
    await db_session.commit()

    response = await client.get("/api/v1/events/metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["total_events"] == 1
    assert "TSLA" in data["symbols"]
    assert data["symbols"]["TSLA"]["count"] == 1
