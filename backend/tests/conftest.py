import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import AsyncGenerator

# Set testing environment BEFORE importing the app
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from app.main import app
from app.core.database import Base
from app.core.dependencies import get_db
from app.models.user import User, RoleEnum
from app.models.student import Student
from app.core.security import get_password_hash, create_access_token

# Create an async engine for SQLite in-memory DB
# poolclass=NullPool is recommended for SQLite in-memory to prevent connection sharing issues across threads,
# but for async tests, standard settings usually work fine.
engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session

# Override the FastAPI dependency
app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(autouse=True)
async def prepare_database():
    """Create all tables before each test and drop them after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session to use within tests."""
    async with TestingSessionLocal() as session:
        yield session

@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession):
    """Create a test student user in the database and return it with a valid token."""
    user = User(
        email="test_student@example.com",
        hashed_password=get_password_hash("password123"),
        role=RoleEnum.STUDENT,
        is_active=True
    )
    db_session.add(user)
    await db_session.flush()

    student = Student(
        user_id=user.id,
        college_id="TEST001",
        branch="Computer Science",
        batch=2026,
        cgpa=8.5,
        active_backlogs=0
    )
    db_session.add(student)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return {"user": user, "token": token, "student": student}

@pytest_asyncio.fixture
async def test_admin(db_session: AsyncSession):
    """Create a test admin user and return it with a valid token."""
    admin = User(
        email="test_admin@example.com",
        hashed_password=get_password_hash("admin123"),
        role=RoleEnum.ADMIN,
        is_active=True
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)

    token = create_access_token({"sub": str(admin.id)})
    return {"user": admin, "token": token}
