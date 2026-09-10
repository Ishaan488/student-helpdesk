"""
Database engine and session configuration.

Sets up SQLAlchemy async engine and session factory.
The `Base` declarative base is what all ORM models will inherit from.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# --- Engine ---
# echo=True in debug mode so you can see the SQL being generated (great for learning)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

# --- Session Factory ---
# expire_on_commit=False prevents attributes from being lazily loaded after commit,
# which doesn't work with async sessions.
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# --- Base Model ---
class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.

    Every model we create (Student, Company, PlacementDrive, etc.)
    will inherit from this. It provides the metadata registry that
    Alembic uses to detect schema changes.
    """

    pass
