# Market Events Service

A high-performance, asynchronous FastAPI service designed to aggregate, normalize, and visualize financial market events from multiple providers. Built with a modular, layered architecture for maximum maintainability and scalability.

---

## 🏗 Architecture & Design Patterns

The project follows **Clean Architecture** principles, separating concerns into distinct layers:

- **API Layer (`app/api/`)**: Handle HTTP requests, routing, and dependency injection.
- **Service Layer (`app/services/`)**: Core business logic, including provider synchronization and normalization.
- **Data Access Layer (`app/crud/`)**: Encapsulated database operations (Repository pattern).
- **Domain Layer (`app/models/` & `app/schemas/`)**: Data structure definitions and Pydantic validation.
- **Core Infrastructure (`app/core/`)**: Shared configuration, database engines, and cache clients.

### System Overview (Mermaid)

```mermaid
graph TD
    User([User/Client]) -->|HTTP| Dashboard[Dashboard UI]
    User -->|HTTP| API[FastAPI API Layer]
    Dashboard -->|Internal Call| Services[Service Layer]
    API -->|DI| Services
    Services -->|Normalized Data| CRUD[CRUD/DAL Layer]
    Services -->|Async HTTP| Providers[External Providers A/B]
    CRUD -->|SQLAlchemy Async| DB[(PostgreSQL)]
    API -->|Cache Check| Redis[(Redis)]
```

---

## 📁 Directory Structure

```text
.
├── app/
│   ├── api/             # API Routers (events, health, dashboard)
│   ├── core/            # Configuration (Pydantic Settings), DB, Redis
│   ├── crud/            # Repository pattern logic
│   ├── models/          # SQLAlchemy ORM models
│   ├── schemas/         # Pydantic schemas (Request/Response)
│   ├── services/        # Provider sync & business logic
│   ├── static/          # CSS/JS for Dashboard
│   ├── templates/       # Jinja2 HTML Templates
│   └── main.py          # Application entry point
├── providers/           # Simulated External Provider APIs
├── tests/               # Modern Async Test Suite (pytest)
├── pyproject.toml       # Poetry Dependencies
└── README.md            # You are here
```

---

## ⚡ Features

- **Multi-Provider Sync**: Concurrent synchronization with Provider A and Provider B.
- **Robust Deduplication**: Intelligent event matching using composite unique constraints.
- **Layered Cache Strategy**: Redis-backed caching with automatic TTL and `X-Cache` headers.
- **Real-time Dashboard**: Interactive dashboard for visualizing market health and event logs.
- **Proactive Health Monitoring**: Comprehensive status checks for DB and Redis connectivity.
- **Async Implementation**: 100% asynchronous I/O using `asyncio`, `asyncpg`, and `redis-py`.

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.12+**
- **Poetry** (Package Manager)
- **PostgreSQL** & **Redis** (Local or via Docker)

### Installation

1. **Install Dependencies**:
   ```bash
   poetry install
   ```

2. **Environment Configuration**:
   Create a `.env` file in the root directory:
   ```env
   DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/market_events
   REDIS_URL=redis://localhost:6379/0
   ```

3. **Database Migration**:
   Models are automatically created on startup via the SQLAlchemy `create_all` hook.

4. **Run the Application**:
   ```bash
   poetry run uvicorn app.main:app --reload
   ```
   The dashboard will be available at `http://localhost:8000`.

---

## 🛠 API Documentation

### Key Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Responsive Dashboard (Jinja2) |
| `GET` | `/api/v1/events` | List events (Cached, Filters: symbols, date, type) |
| `POST` | `/api/v1/events/sync` | Trigger Provider Synchronization |
| `GET` | `/api/v1/events/metrics` | System-wide performance & count metrics |
| `GET` | `/api/v1/health` | Deep health check (DB/Redis) |

Detailed interactive docs are available at `/docs` (Swagger UI).

---

## 🧪 Testing

The project uses `pytest` with `pytest-asyncio` and `pytest-mock`. The test suite features database and redis isolation for every test run.

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app
```

---

## 💅 Linting & Formatting

We use **Ruff** for high-performance linting and formatting.

```bash
# Lint check
poetry run ruff check .

# Format code
poetry run ruff format .
```

---

## 📝 License

This project is prepared for assessment purposes. Refer to the internal evaluation guidelines for redistribution.