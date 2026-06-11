# Market Service

Production-grade stock market data microservice built with FastAPI, Clean Architecture, and DDD.

## Stack

- Python 3.13, FastAPI, SQLAlchemy 2.0 (async), Alembic, PostgreSQL
- Redis, Kafka (aiokafka), Pydantic v2, structlog, uv

## Quick Start

```bash
# Install dependencies
uv sync --all-extras

# Copy environment
cp .env.example .env

# Start infrastructure
docker compose up -d postgres redis kafka

# Run migrations
uv run alembic upgrade head

# Start service
uv run uvicorn main:app --reload
```

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/market/quote/{symbol}` | Latest quote |
| GET | `/market/candles` | Historical OHLCV |
| GET | `/market/search` | Symbol search |
| POST | `/watchlist` | Create watchlist |
| GET | `/watchlist` | List watchlists |
| DELETE | `/watchlist/{symbol}` | Remove symbol |
| WS | `/ws/market` | Live quotes |

## Tests

```bash
uv run pytest -v
```

## Docker

```bash
# Start in background (no logs in terminal)
docker compose up --build -d

# Stop
docker compose down

# View logs only when you need them
docker compose logs -f market-service
```

**Important:** After starting, open your browser to:

| What | URL |
|------|-----|
| API docs (Swagger) | **http://localhost:8001/docs** |
| Health check | http://localhost:8001/health |
| Example quote | http://localhost:8001/market/quote/AAPL |

> Port **8001** is used (not 8000) because something on your machine already uses 8000.
> Wait ~30–60 seconds on first start while Kafka/Postgres become healthy.
