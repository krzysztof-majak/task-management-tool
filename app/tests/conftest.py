from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.tests.factories.model_factories import ProjectFactory, TaskFactory

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest.fixture(scope="function")
async def test_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.begin() as conn:
        session = TestSessionLocal(bind=conn)
        ProjectFactory.bind_session(session)
        TaskFactory.bind_session(session)
        app.dependency_overrides[get_db] = lambda: session

        yield session

        await session.rollback()
        await session.close()


@pytest.fixture(scope="module", autouse=True)
async def initialize_test_db_schema() -> AsyncGenerator[None, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    await test_engine.dispose()


@pytest.fixture()
async def test_api_client(test_db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
