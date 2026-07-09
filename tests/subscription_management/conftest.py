from typing import TYPE_CHECKING

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from subscription_management.logic.database import create_and_initialize_async_engine
from subscription_management.logic.main import app

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator
    from pathlib import Path

    from fastapi import FastAPI


@pytest.fixture
def _app(_engine: AsyncEngine) -> Generator[FastAPI]:  # pyright: ignore[reportUnusedFunction]
    app.state.engine = _engine
    yield app
    del app.state.engine


@pytest.fixture
def _database_url(tmp_path: Path) -> str:  # pyright: ignore[reportUnusedFunction]
    file = tmp_path / "database.sqlite"
    return f"sqlite+aiosqlite:///{file}"


@pytest.fixture
async def _engine(_database_url: str) -> AsyncGenerator[AsyncEngine]:  # pyright: ignore[reportUnusedFunction]
    engine = await create_and_initialize_async_engine(_database_url)
    await engine.dispose()  # makes the tests start with new and unused connections
    yield engine
    await engine.dispose()


@pytest.fixture
async def client(_app: FastAPI) -> AsyncGenerator[AsyncClient]:
    # The database setup logic for `app` lives in its `lifespan` function.
    # Unfortunately, `ASGITransport` and `AsyncClient` do not run `lifespan` events.
    # Therefore, we use the `_app` fixture which takes care of the database setup.
    transport = ASGITransport(_app)
    async with AsyncClient(
        base_url="http://test", follow_redirects=True, transport=transport
    ) as client:
        yield client


@pytest.fixture
async def session(_engine: AsyncEngine) -> AsyncGenerator[AsyncSession]:
    async with AsyncSession(_engine) as session:
        yield session
