"""Shared pytest fixtures."""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.brokers.base import MarketProvider
from app.cache.quote_cache import QuoteCache
from app.db.base import Base
from app.kafka.producer import KafkaEventProducer
from app.schemas.market import CandleInterval, OHLCVCandle, QuoteResponse, SearchResult
from app.services.market_service import MarketService
from app.services.watchlist_service import WatchlistService
from app.repositories.watchlist_repository import WatchlistRepository


class MockMarketProvider(MarketProvider):
    """Test double for market provider."""

    async def get_quote(self, symbol: str) -> QuoteResponse:
        if symbol == "INVALID":
            from app.exceptions import SymbolNotFound
            raise SymbolNotFound(symbol)
        return QuoteResponse(
            symbol=symbol.upper(),
            exchange="NASDAQ",
            price=100.0,
            change=1.5,
            volume=500000,
            timestamp=datetime.now(UTC),
        )

    async def get_candles(
        self,
        symbol: str,
        interval: CandleInterval,
        from_dt: datetime,
        to_dt: datetime,
    ) -> list[OHLCVCandle]:
        return [
            OHLCVCandle(
                timestamp=from_dt,
                open=100.0,
                high=105.0,
                low=99.0,
                close=103.0,
                volume=10000,
            )
        ]

    async def search_symbol(self, query: str) -> list[SearchResult]:
        return [
            SearchResult(symbol="AAPL", exchange="NASDAQ", company_name="Apple Inc."),
        ]

    async def subscribe_ticks(self, symbols: list[str]):
        quote = await self.get_quote(symbols[0])
        yield quote

    async def fetch_news(self, symbol: str | None = None) -> list[dict]:
        return [{
            "symbol": "AAPL",
            "headline": "Test headline",
            "url": "https://example.com",
            "published_at": datetime.now(UTC).isoformat(),
        }]


@pytest.fixture
def mock_provider() -> MockMarketProvider:
    return MockMarketProvider()


@pytest.fixture
def mock_redis() -> AsyncMock:
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock()
    redis.delete = AsyncMock()
    return redis


@pytest.fixture
def mock_kafka() -> AsyncMock:
    kafka = AsyncMock(spec=KafkaEventProducer)
    kafka.publish_quote_updated = AsyncMock()
    kafka.publish_tick = AsyncMock()
    kafka.publish_news = AsyncMock()
    return kafka


@pytest.fixture
def quote_cache(mock_redis: AsyncMock) -> QuoteCache:
    return QuoteCache(mock_redis)


@pytest.fixture
def market_service(mock_provider: MockMarketProvider, quote_cache: QuoteCache, mock_kafka: AsyncMock) -> MarketService:
    return MarketService(mock_provider, quote_cache, mock_kafka)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def watchlist_service(db_session: AsyncSession) -> WatchlistService:
    return WatchlistService(WatchlistRepository(db_session))


@pytest_asyncio.fixture
async def test_app():
    """Create test FastAPI app without background workers."""
    from contextlib import asynccontextmanager

    from fastapi import FastAPI

    from app.api.router import api_router
    from app.exceptions.base import AppException
    from app.exceptions.handlers import app_exception_handler, unhandled_exception_handler
    from app.middleware.user_context import UserContextMiddleware

    @asynccontextmanager
    async def test_lifespan(_app: FastAPI):
        yield

    app = FastAPI(lifespan=test_lifespan)
    app.add_middleware(UserContextMiddleware)
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
    app.include_router(api_router)
    return app


@pytest_asyncio.fixture
async def client(test_app) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
