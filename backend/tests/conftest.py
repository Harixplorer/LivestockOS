import asyncio
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.api.deps import get_db
from app.db.base import Base
from app.main import app
from app.services.auth_service import register_user
from app.schemas.auth import RegisterRequest

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def prepare_database():
    """Create all tables before each test and drop them after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def test_user(client: AsyncClient):
    """Register and return a standard test farmer user."""
    req_data = {
        "email": "testfarmer@livestockos.io",
        "password": "password123",
        "full_name": "Test Farmer",
        "phone_number": "9876543210",
        "farm_name": "Green Valley Test Farm",
        "village": "Test Village",
        "district": "Test District",
        "state": "Test State"
    }
    res = await client.post("/auth/register", json=req_data)
    assert res.status_code == 201
    return res.json()


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, test_user) -> dict:
    """Return authorization bearer headers for test_user."""
    login_res = await client.post(
        "/auth/login",
        json={"email": "testfarmer@livestockos.io", "password": "password123"}
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def second_auth_headers(client: AsyncClient) -> dict:
    """Return authorization bearer headers for a distinct second user (tenant isolation)."""
    req_data = {
        "email": "otherfarmer@livestockos.io",
        "password": "password123",
        "full_name": "Other Farmer",
        "phone_number": "9999999999",
        "farm_name": "Isolated Other Farm"
    }
    res = await client.post("/auth/register", json=req_data)
    assert res.status_code == 201

    login_res = await client.post(
        "/auth/login",
        json={"email": "otherfarmer@livestockos.io", "password": "password123"}
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
