import typing

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)

from app.database import AsyncSessionDep, initialize_engine
from app.main import app

if typing.TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator
    from pathlib import Path

    from fastapi import FastAPI


@pytest.fixture
async def _engine(tmp_path: Path) -> AsyncGenerator[AsyncEngine]:  # pyright: ignore[reportUnusedFunction]
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{tmp_path / 'database.sqlite3'}", echo=True
    )
    await initialize_engine(engine)
    await engine.dispose()
    yield engine
    await engine.dispose()


@pytest.fixture
def _app(_engine: AsyncEngine) -> Generator[FastAPI]:  # pyright: ignore[reportUnusedFunction]
    async def get_session() -> AsyncGenerator[AsyncSession]:
        async with AsyncSession(_engine) as async_session, async_session.begin():
            yield async_session

    app.dependency_overrides = {
        typing.get_args(AsyncSessionDep.__value__)[1].dependency: get_session
    }
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
async def client(_app: FastAPI) -> AsyncGenerator[AsyncClient]:
    transport = ASGITransport(_app)
    async with AsyncClient(
        base_url="http://test", follow_redirects=True, transport=transport
    ) as client:
        yield client


@pytest.fixture
async def session(_engine: AsyncEngine) -> AsyncGenerator[AsyncSession]:
    async with AsyncSession(_engine) as async_session:
        yield async_session
