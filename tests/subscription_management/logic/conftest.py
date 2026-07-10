from typing import TYPE_CHECKING

import pytest
from httpx import ASGITransport, AsyncClient

from subscription_management.logic.main import app

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator

    from fastapi import FastAPI
    from sqlalchemy.ext.asyncio import AsyncEngine


@pytest.fixture
def _app(_engine: AsyncEngine) -> Generator[FastAPI]:  # pyright: ignore[reportUnusedFunction]
    # The database setup logic for `app` lives in its `lifespan` function.
    # Unfortunately, `ASGITransport` and `AsyncClient` do not run `lifespan` events.
    # Therefore, we use the `_app` fixture which takes care of the database setup.
    app.state.engine = _engine
    yield app
    del app.state.engine


@pytest.fixture
async def client(_app: FastAPI) -> AsyncGenerator[AsyncClient]:
    transport = ASGITransport(_app)
    async with AsyncClient(
        base_url="http://test", follow_redirects=True, transport=transport
    ) as client:
        yield client
