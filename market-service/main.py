"""Market Service application entry point."""

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.exceptions.base import AppException
from app.exceptions.handlers import app_exception_handler, unhandled_exception_handler
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.user_context import UserContextMiddleware
from app.startup.lifespan import lifespan

setup_logging()
settings = get_settings()

app = FastAPI(
    title="Market Service",
    description="Production-grade stock market data microservice with real-time quotes, "
    "historical candles, watchlists, and WebSocket streaming.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(UserContextMiddleware)

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(api_router)
