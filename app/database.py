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


async def create_and_initialize_engine() -> AsyncEngine:
    def enable_foreign_keys(connection: DBAPIConnection, _: object) -> None:
        with closing(connection.cursor()) as cursor:
            cursor.execute("PRAGMA foreign_keys=ON")

    database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///database.sqlite3")
    async_engine = create_async_engine(database_url, echo=True)

    if not event.contains(async_engine.sync_engine, "connect", enable_foreign_keys):
        event.listen(async_engine.sync_engine, "connect", enable_foreign_keys)

    await create_all_tables(async_engine)

    return async_engine


async def get_async_session(request: Request) -> AsyncGenerator[AsyncSession]:
    async with (
        AsyncSession(
            request.app.state.async_engine, expire_on_commit=False
        ) as async_session,
        async_session.begin(),
    ):
        yield async_session


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    async_engine = await create_and_initialize_engine()
    app.state.async_engine = async_engine
    yield
    await async_engine.dispose()


type AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session)]
