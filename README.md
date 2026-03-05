Market Events Service
=====================

Overview
--------

The **Market Events Service** is a **FastAPI** application that aggregates financial market events from multiple providers, normalizes them into a unified schema, stores them in PostgreSQL with deduplication, caches results in Redis, and exposes a REST API and a dashboard for visualization.

The service supports **earnings, dividends, splits, and economic events**, and allows clients to query events efficiently with filtering, pagination, and caching.

Table of Contents
-----------------

1. Features
2. Assumptions
3. Architecture
4. Data Models
5. API Endpoints
6. Dashboard
7. Providers
8. Setup & Installation
9. Testing
10. Future Improvements

Features
--------

*   Fetches events from two simulated providers (ProviderA and ProviderB).
*   Normalizes events into a **unified schema**.
*   Stores events in **PostgreSQL**, avoiding duplicates using unique constraints.
*   Tracks last sync per symbol using `EventSyncLog`.
*   Caches API responses in **Redis** with TTL and supports cache headers (`X-Cache: HIT / MISS`).
*   Provides a REST API and a **dashboard** with filters, metrics, and event listing.
*   Supports forced sync and incremental sync per symbol.
*   Utilizes a professional **layered architecture** (API, Service, CRUD, Models, Schemas).

Assumptions
-----------

1. **Provider simulation**:
   *   `providers/` folder simulates external APIs.
   *   Each provider has different formats and may return overlapping events with different IDs.
2. **Deduplication**:
   *   Events are considered duplicates if they share `(symbol, event_type, event_date)`.
   *   Provider-specific `provider_event_id` is stored for reference.
3. **Event times**:
   *   If provider events are missing time, default is `00:00:00`.
   *   All timestamps stored in UTC.
4. **Caching**:
   *   `/api/v1/events` responses cached for 10 minutes.
   *   Individual events cached per ID.
5. **Sync logic**:
   *   By default (`force: false`), symbols synced in the last hour are skipped.
   *   `force: true` always fetches fresh events from providers.
6. **Frontend dashboard**:
   *   Displays live system metrics and latest events.
   *   Uses **Jinja2 templates** and **static assets** for a premium UI.
   *   Fetched directly from the service layer for performance.

Architecture
------------

The service is built with a modular design to ensure high maintainability:

*   **FastAPI**: Handles high-performance asynchronous REST API and routing.
*   **SQLAlchemy**: Uses `AsyncSession` for efficient asynchronous database operations.
*   **Redis**: Used for high-speed caching and tracking synchronization heartbeats.
*   **Jinja2**: Renders the server-side dashboard with modern CSS and Inter typography.

Data Models
-----------

### Event

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique identifier (Primary Key). |
| `symbol` | String | Stock symbol (e.g., AAPL). |
| `event_type` | String | Type of event (earnings, dividend, split, economic). |
| `event_date` | DateTime | Scheduled date/time in UTC. |
| `title` | String | Normalized human-readable title. |
| `details` | JSON | Raw data payload from the provider. |
| `source` | String | Data source (provider_a / provider_b). |
| `provider_event_id` | String | Original ID from the external provider. |
| `created_at` | DateTime | Record creation timestamp. |
| `updated_at` | DateTime | Record last update timestamp. |

**Unique Constraint**: `(symbol, event_type, event_date)`

### EventSyncLog

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key. |
| `symbol` | String | The symbol being tracked. |
| `last_synced_at` | DateTime | Last successful synchronization (UTC). |

API Endpoints
-------------

### GET /api/v1/events

Fetch events with optional filters.

**Query Params**:
- `symbols`: Comma-separated symbols (e.g., `AAPL,MSFT`)
- `event_type`: Filter by type (e.g., `earnings`)
- `from_date`: Start date (YYYY-MM-DD)
- `to_date`: End date (YYYY-MM-DD)
- `skip`: Pagination offset (Default: 0)
- `limit`: Pagination limit (Default: 50)

### GET /api/v1/events/metrics

Returns system-wide metrics including total event counts and per-symbol statistics.

### GET /api/v1/events/{event_id}

Fetch a single event by its UUID.

### POST /api/v1/events/sync

Trigger synchronization with providers for specified symbols.

**Request Body**:
```json
{
  "symbols": ["AAPL", "MSFT"],
  "force": false
}
```

### GET /api/v1/health

Returns service health status for the API, Database, and Redis.

Dashboard
---------

*   Located at the root URL `/`.
*   **Stats Grid**: Displays total processed events and count of tracked symbols.
*   **Symbol Stats**: Detailed breakdown of events per symbol with last sync timestamps.
*   **Recent Events**: A table of the latest 50 market events.
*   **Modern Design**: Features a premium dark-themed UI with responsive layouts.

Providers
---------

*   **ProviderA** and **ProviderB** are simulated in the `providers/` directory.
*   The application handles varying response structures and normalizes them into the unified internal model.

Setup & Installation
--------------------

### Requirements
*   Python 3.12+
*   Poetry
*   Docker & Docker Compose

### Steps

1. **Clone the repository** and navigate to the project root.
2. **Install dependencies**:
   ```bash
   poetry install
   ```
3. **Environment Setup**: Create a `.env` file based on the codebase needs (Database and Redis URLs).
4. **Infrastructure**: Start PostgreSQL and Redis via Docker.
   ```bash
   docker-compose up -d
   ```
5. **Start the server**:
   ```bash
   poetry run uvicorn app.main:app --reload --port 8000
   ```
6. **Access**: Open `http://localhost:8000` in your browser.

Testing
-------

Run the comprehensive async test suite using pytest:
```bash
poetry run pytest
```

Linting
-------

Maintain code quality with Ruff:
```bash
poetry run ruff check .
```