"""WebSocket routes for live market data."""

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.brokers.factory import get_market_provider
from app.cache.quote_cache import QuoteCache
from app.cache.redis_client import get_redis
from app.core.logging import get_logger
from app.schemas.websocket import QuotePushMessage, SubscribeMessage

router = APIRouter()
logger = get_logger(__name__)


@router.websocket("/ws/market")
async def market_websocket(websocket: WebSocket) -> None:
    """Live quote WebSocket endpoint.

    Client sends: {"symbols": ["AAPL", "TSLA", "MSFT"]}
    Server pushes latest prices periodically.
    """
    await websocket.accept()
    provider = get_market_provider()
    redis = await get_redis()
    cache = QuoteCache(redis)

    try:
        raw = await websocket.receive_text()
        subscribe = SubscribeMessage.model_validate(json.loads(raw))
        symbols = subscribe.symbols
        logger.info("websocket_subscribed", symbols=symbols)

        async for quote in provider.subscribe_ticks(symbols):
            # Update cache on each tick
            await cache.set(quote)

            push = QuotePushMessage(
                symbol=quote.symbol,
                exchange=quote.exchange,
                price=quote.price,
                change=quote.change,
                volume=quote.volume,
                timestamp=quote.timestamp.isoformat(),
            )
            await websocket.send_text(push.model_dump_json())

    except WebSocketDisconnect:
        logger.info("websocket_disconnected")
    except Exception as exc:
        logger.warning("websocket_error", error=str(exc))
        await websocket.close(code=1011)
