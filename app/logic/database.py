from contextlib import asynccontextmanager, closing
from typing import TYPE_CHECKING, Annotated

from fastapi import FastAPI, Request  # noqa: TC002
from fastapi_dependency import Depends
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from app.data_structures.models import create_all_tables

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqlalchemy.engine.interfaces import DBAPIConnection

__docformat__ = "google"


def _enable_foreign_keys(engine: AsyncEngine) -> None:
    if not event.contains(
        engine.sync_engine, "connect", _enable_foreign_keys_for_connection
    ):
        event.listen(engine.sync_engine, "connect", _enable_foreign_keys_for_connection)


def _enable_foreign_keys_for_connection(connection: DBAPIConnection, _: object) -> None:
    with closing(connection.cursor()) as cursor:
        cursor.execute("PRAGMA foreign_keys=ON")


def _get_async_engine(request: Request) -> AsyncEngine:  # pragma: no cover
    return request.app.state.engine


async def _get_async_session(
    engine: _AsyncEngineDep,
) -> AsyncGenerator[AsyncSession]:  # pragma: no cover
    """Manages the complete lifecycle of the `AsyncSession`.

    See: https://docs.sqlalchemy.org/en/20/orm/session_basics.html#when-do-i-construct-a-session-when-do-i-commit-it-and-when-do-i-close-it
    """
    async with AsyncSession(engine, expire_on_commit=False) as session, session.begin():
        yield session


@asynccontextmanager
async def async_engine_lifespan(
    app: FastAPI,
) -> AsyncGenerator[None]:  # pragma: no cover
    engine = await create_and_initialize_async_engine()
    app.state.engine = engine
    yield
    del app.state.engine
    await engine.dispose()


async def create_and_initialize_async_engine(
    url: str = "sqlite+aiosqlite:///database.sqlite3",
) -> AsyncEngine:
    engine = create_async_engine(url, echo=True)
    _enable_foreign_keys(engine)
    await create_all_tables(engine)
    return engine


type _AsyncEngineDep = Annotated[
    AsyncEngine, Depends(_get_async_engine, run_in_threadpool=True)
]
type AsyncSessionDep = Annotated[
    AsyncSession, Depends(_get_async_session, run_in_threadpool=True)
]
