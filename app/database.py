import os
from contextlib import asynccontextmanager, closing
from typing import TYPE_CHECKING, Annotated

from fastapi import Depends, FastAPI, Request
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from app.data_structures.models import create_all_tables

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqlalchemy.engine.interfaces import DBAPIConnection


def _create_async_engine() -> AsyncEngine:
    database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///database.sqlite3")
    return create_async_engine(database_url, echo=True)


def _enable_fks_for_connection(connection: "DBAPIConnection", _: object) -> None:
    with closing(connection.cursor()) as cursor:
        cursor.execute("PRAGMA foreign_keys=ON")


def _enable_foreign_keys(engine: AsyncEngine) -> None:
    if not event.contains(engine.sync_engine, "connect", _enable_fks_for_connection):
        event.listen(engine.sync_engine, "connect", _enable_fks_for_connection)


def _get_async_engine(request: Request) -> AsyncEngine:  # pragma: no cover
    return request.app.state.engine


async def _get_async_session(
    engine: _AsyncEngineDep,
) -> AsyncGenerator[AsyncSession]:  # pragma: no cover
    async with AsyncSession(engine, expire_on_commit=False) as session, session.begin():
        yield session


async def create_and_initialize_async_engine() -> AsyncEngine:
    engine = _create_async_engine()
    _enable_foreign_keys(engine)
    await create_all_tables(engine)
    return engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:  # pragma: no cover
    engine = await create_and_initialize_async_engine()
    app.state.engine = engine
    yield
    del app.state.engine
    await engine.dispose()


type _AsyncEngineDep = Annotated[AsyncEngine, Depends(_get_async_engine)]
type AsyncSessionDep = Annotated[AsyncSession, Depends(_get_async_session)]
