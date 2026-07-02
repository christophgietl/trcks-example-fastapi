import os
from contextlib import asynccontextmanager, closing
from typing import TYPE_CHECKING, Annotated

from fastapi import Depends
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.data_structures.models import create_all_tables

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqlalchemy.engine.interfaces import DBAPIConnection
    from sqlalchemy.ext.asyncio import AsyncEngine
    from sqlalchemy.pool import ConnectionPoolEntry


def _enable_foreign_keys(connection: DBAPIConnection, _: ConnectionPoolEntry) -> None:
    with closing(connection.cursor()) as cursor:
        cursor.execute("PRAGMA foreign_keys=ON")


async def initialize_engine(engine: AsyncEngine) -> None:
    if not event.contains(engine.sync_engine, "connect", _enable_foreign_keys):
        event.listen(engine.sync_engine, "connect", _enable_foreign_keys)
    await create_all_tables(engine)


_async_engine: AsyncEngine


@asynccontextmanager
async def lifespan(_: object) -> AsyncGenerator[None]:  # pragma: no cover
    database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///database.sqlite3")
    global _async_engine  # noqa: PLW0603
    _async_engine = create_async_engine(database_url, echo=True)
    await initialize_engine(_async_engine)
    yield
    await _async_engine.dispose()


async def _get_async_session() -> AsyncGenerator[AsyncSession]:  # pragma: no cover
    """Manages the complete lifecycle of the `AsyncSession`.

    See: https://docs.sqlalchemy.org/en/20/orm/session_basics.html#when-do-i-construct-a-session-when-do-i-commit-it-and-when-do-i-close-it
    """
    async with (
        AsyncSession(_async_engine, expire_on_commit=False) as async_session,
        async_session.begin(),
    ):
        yield async_session


type AsyncSessionDep = Annotated[AsyncSession, Depends(_get_async_session)]
