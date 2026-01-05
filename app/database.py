from collections.abc import AsyncIterator  # noqa: TC003
from contextlib import asynccontextmanager
from typing import Annotated, TypeAlias

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.data_structures.models import set_pragmas_and_create_all_tables

_async_engine = create_async_engine("sqlite+aiosqlite:///database.sqlite3", echo=True)


@asynccontextmanager
async def lifespan(_: object) -> AsyncIterator[None]:  # pragma: no cover
    await set_pragmas_and_create_all_tables(_async_engine)
    yield
    await _async_engine.dispose()


_async_sessionmaker = async_sessionmaker(_async_engine, expire_on_commit=False)


async def _get_async_session() -> AsyncIterator[AsyncSession]:  # pragma: no cover
    """Manages the complete lifecycle of the `AsyncSession`.

    See: https://docs.sqlalchemy.org/en/20/orm/session_basics.html#when-do-i-construct-a-session-when-do-i-commit-it-and-when-do-i-close-it
    """
    async with _async_sessionmaker() as async_session, async_session.begin():
        yield async_session


# FastAPI does not support the type keyword when used for dependencies
# as of October 2025 (see https://github.com/fastapi/fastapi/issues/10719):
AsyncSessionDep: TypeAlias = Annotated[  # noqa: UP040
    AsyncSession, Depends(_get_async_session)
]
