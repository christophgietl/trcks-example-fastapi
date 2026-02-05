import typing
from collections.abc import AsyncIterator  # noqa: TC003

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)

from app.data_structures.models import set_pragmas_and_create_all_tables
from app.database import AsyncSessionDep
from app.main import app

if typing.TYPE_CHECKING:
    from collections.abc import Iterator

    from fastapi import FastAPI


@pytest.fixture
async def _engine() -> AsyncIterator[AsyncEngine]:  # pyright: ignore[reportUnusedFunction]
    engine = create_async_engine("sqlite+aiosqlite://", echo=True)
    await set_pragmas_and_create_all_tables(engine)
    yield engine
    await engine.dispose()


@pytest.fixture
def _app(_engine: AsyncEngine) -> Iterator[FastAPI]:  # pyright: ignore[reportUnusedFunction]
    async def get_session() -> AsyncIterator[AsyncSession]:
        async with AsyncSession(_engine) as async_session, async_session.begin():
            yield async_session

    app.dependency_overrides = {
        typing.get_args(AsyncSessionDep.__value__)[1].dependency: get_session
    }
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
async def client(_app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(_app)
    async with AsyncClient(
        base_url="http://test", follow_redirects=True, transport=transport
    ) as client:
        yield client


@pytest.fixture
async def session(_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    async with AsyncSession(_engine) as async_session:
        yield async_session
