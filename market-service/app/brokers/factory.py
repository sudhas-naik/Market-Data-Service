"""Factory for pluggable market data providers."""

from functools import lru_cache

from app.brokers.base import MarketProvider
from app.brokers.mock_provider import MockProvider
from app.core.config import Settings, get_settings


def create_market_provider(settings: Settings) -> MarketProvider:
    """Instantiate the configured market provider.

    Future providers can be registered here:
    - polygon -> PolygonProvider
    - alpaca -> AlpacaProvider
    - yahoo -> YahooProvider
    - zerodha -> ZerodhaProvider
    - upstox -> UpstoxProvider
    """
    providers: dict[str, type[MarketProvider]] = {
        "mock": MockProvider,
    }

    provider_cls = providers.get(settings.market_provider)
    if provider_cls is None:
        raise ValueError(f"Unknown market provider: {settings.market_provider}")

    return provider_cls()


@lru_cache
def get_market_provider() -> MarketProvider:
    """Return cached market provider singleton."""
    return create_market_provider(get_settings())
