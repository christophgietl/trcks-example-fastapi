from contextlib import asynccontextmanager, closing
from typing import TYPE_CHECKING, Annotated

from fastapi import Depends
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.data_structures.models import create_all_tables

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqlalchemy.engine.interfaces import DBAPIConnection
    from sqlalchemy.ext.asyncio import AsyncEngine
    from sqlalchemy.pool import ConnectionPoolEntry


def _enable_foreign_keys(
    dbapi_connection: DBAPIConnection, _: ConnectionPoolEntry
) -> None:
    with closing(dbapi_connection.cursor()) as cursor:
        cursor.execute("PRAGMA foreign_keys=ON")


def enable_foreign_keys_for_engine(engine: AsyncEngine) -> None:
    if not event.contains(engine.sync_engine, "connect", _enable_foreign_keys):
        event.listen(engine.sync_engine, "connect", _enable_foreign_keys)


_async_engine = create_async_engine("sqlite+aiosqlite:///database.sqlite3", echo=True)
enable_foreign_keys_for_engine(_async_engine)


@asynccontextmanager
async def lifespan(_: object) -> AsyncGenerator[None]:  # pragma: no cover
    await create_all_tables(_async_engine)
    yield
    await _async_engine.dispose()


_async_sessionmaker = async_sessionmaker(_async_engine, expire_on_commit=False)


async def _get_async_session() -> AsyncGenerator[AsyncSession]:  # pragma: no cover
    """Manages the complete lifecycle of the `AsyncSession`.

    See: https://docs.sqlalchemy.org/en/20/orm/session_basics.html#when-do-i-construct-a-session-when-do-i-commit-it-and-when-do-i-close-it
    """
    async with _async_sessionmaker() as async_session, async_session.begin():
        yield async_session


type AsyncSessionDep = Annotated[AsyncSession, Depends(_get_async_session)]
