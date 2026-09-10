"""
FastAPI dependency injection.

Dependencies are functions that FastAPI calls automatically before your
route handler runs. They're the standard way to provide shared resources
(database sessions, current user, etc.) to endpoints.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield a database session for the duration of a single request.

    Usage in a route:
        @router.get("/example")
        async def example(db: AsyncSession = Depends(get_db)):
            ...

    The session is automatically closed when the request finishes,
    even if an exception occurs (thanks to the finally block).
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
