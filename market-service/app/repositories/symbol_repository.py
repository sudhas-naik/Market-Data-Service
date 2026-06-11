"""Symbol data access repository."""

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.symbol import Symbol


class SymbolRepository:
    """Repository for symbol CRUD and search operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_symbol(self, symbol: str) -> Symbol | None:
        result = await self._session.execute(
            select(Symbol).where(Symbol.symbol == symbol.upper())
        )
        return result.scalar_one_or_none()

    async def search(self, query: str, limit: int = 20) -> list[Symbol]:
        pattern = f"%{query.lower()}%"
        result = await self._session.execute(
            select(Symbol)
            .where(
                Symbol.is_active.is_(True),
                or_(
                    Symbol.symbol.ilike(pattern),
                    Symbol.company_name.ilike(pattern),
                ),
            )
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, symbol: Symbol) -> Symbol:
        self._session.add(symbol)
        await self._session.flush()
        await self._session.refresh(symbol)
        return symbol

    async def get_all_active(self) -> list[Symbol]:
        result = await self._session.execute(
            select(Symbol).where(Symbol.is_active.is_(True))
        )
        return list(result.scalars().all())
