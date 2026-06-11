"""Main API router aggregating all route modules."""

from fastapi import APIRouter

from app.api.routes import health, market, watchlist, websocket

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(market.router, prefix="/market", tags=["Market"])
api_router.include_router(watchlist.router, prefix="/watchlist", tags=["Watchlist"])
api_router.include_router(websocket.router, tags=["WebSocket"])
