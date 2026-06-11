"""Market data API routes."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies.market import get_market_service
from app.schemas.common import APIResponse
from app.schemas.market import (
    CandleInterval,
    CandleResponse,
    QuoteResponse,
    SearchResponse,
)
from app.services.market_service import MarketService

router = APIRouter()


@router.get(
    "/quote/{symbol}",
    response_model=APIResponse[QuoteResponse],
    summary="Get latest quote",
    description="Returns the latest market quote for a symbol. Checks Redis cache first.",
)
async def get_quote(
    symbol: str,
    service: Annotated[MarketService, Depends(get_market_service)],
) -> APIResponse[QuoteResponse]:
    quote = await service.get_quote(symbol)
    return APIResponse(data=quote)


@router.get(
    "/candles",
    response_model=APIResponse[CandleResponse],
    summary="Get historical candles",
    description="Returns OHLCV candle data for a symbol within a date range.",
)
async def get_candles(
    service: Annotated[MarketService, Depends(get_market_service)],
    symbol: str = Query(..., min_length=1, max_length=20, examples=["AAPL"]),
    interval: CandleInterval = Query(CandleInterval.ONE_DAY, examples=["1d"]),
    from_dt: datetime = Query(..., alias="from", examples=["2026-01-01T00:00:00Z"]),
    to_dt: datetime = Query(..., alias="to", examples=["2026-06-01T00:00:00Z"]),
) -> APIResponse[CandleResponse]:
    candles = await service.get_candles(symbol.upper(), interval, from_dt, to_dt)
    return APIResponse(data=candles)


@router.get(
    "/search",
    response_model=APIResponse[SearchResponse],
    summary="Search symbols",
    description="Search for stock symbols by ticker or company name.",
)
async def search_symbols(
    service: Annotated[MarketService, Depends(get_market_service)],
    q: str = Query(..., min_length=1, max_length=50, examples=["app"]),
) -> APIResponse[SearchResponse]:
    results = await service.search_symbols(q)
    return APIResponse(data=results)
