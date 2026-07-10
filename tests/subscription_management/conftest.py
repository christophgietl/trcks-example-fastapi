from typing import TYPE_CHECKING

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from subscription_management.logic.database import create_and_initialize_async_engine

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator
    from pathlib import Path


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
async def session(_engine: AsyncEngine) -> AsyncGenerator[AsyncSession]:
    async with AsyncSession(_engine) as session:
        yield session
