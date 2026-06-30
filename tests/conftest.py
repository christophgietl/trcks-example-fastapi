from typing import TYPE_CHECKING

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.database import create_engine, get_engine
from app.main import app

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator
    from pathlib import Path

    from fastapi import FastAPI


@pytest.fixture
async def _engine(tmp_path: Path) -> AsyncGenerator[AsyncEngine]:  # pyright: ignore[reportUnusedFunction]
    database_file = tmp_path / "database.sqlite3"
    engine = await create_engine(f"sqlite+aiosqlite:///{database_file}")
    await engine.dispose()  # avoids reusing the connection used by table initialization
    yield engine
    await engine.dispose()


@pytest.fixture
def _app(_engine: AsyncEngine) -> Generator[FastAPI]:  # pyright: ignore[reportUnusedFunction]
    def _get_test_engine() -> AsyncEngine:
        return _engine

    app.dependency_overrides[get_engine] = _get_test_engine
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
