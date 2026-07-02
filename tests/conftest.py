from typing import TYPE_CHECKING

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.database import create_and_initialize_engine
from app.main import app

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator
    from pathlib import Path

    from fastapi import FastAPI


@pytest.fixture
def _app(_engine: AsyncEngine) -> Generator[FastAPI]:  # pyright: ignore[reportUnusedFunction]
    app.state.async_engine = _engine
    yield app
    del app.state.async_engine


@pytest.fixture(autouse=True)
def _database_url(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:  # pyright: ignore[reportUnusedFunction]
    file = tmp_path / "database.sqlite"
    url = f"sqlite+aiosqlite:///{file}"
    monkeypatch.setenv("DATABASE_URL", url)


@pytest.fixture
async def _engine() -> AsyncGenerator[AsyncEngine]:  # pyright: ignore[reportUnusedFunction]
    engine = await create_and_initialize_engine()
    await engine.dispose()  # avoids reusing the connection used by `initialize_engine`
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
