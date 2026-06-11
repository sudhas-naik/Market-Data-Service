"""Application startup and shutdown lifecycle."""

from app.startup.lifespan import lifespan

__all__ = ["lifespan"]
