from contextlib import asynccontextmanager, closing
from typing import TYPE_CHECKING, Annotated

from fastapi import Depends, FastAPI, Request
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from app.data_structures.models import create_all_tables

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqlalchemy.engine.interfaces import DBAPIConnection
    from sqlalchemy.pool import ConnectionPoolEntry


def _enable_foreign_keys(connection: DBAPIConnection, _: ConnectionPoolEntry) -> None:
    with closing(connection.cursor()) as cursor:
        cursor.execute("PRAGMA foreign_keys=ON")


async def create_engine(
    url: str = "sqlite+aiosqlite:///database.sqlite3",
) -> AsyncEngine:
    engine = create_async_engine(url, echo=True)
    event.listen(engine.sync_engine, "connect", _enable_foreign_keys)
    await create_all_tables(engine)
    return engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    engine = await create_engine()
    app.state.engine = engine
    try:
        yield
    finally:
        await engine.dispose()


def get_engine(request: Request) -> AsyncEngine:
    return request.app.state.engine


async def get_async_session(
    engine: Annotated[AsyncEngine, Depends(get_engine)],
) -> AsyncGenerator[AsyncSession]:
    async with AsyncSession(engine) as async_session, async_session.begin():
        yield async_session


type AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session)]
