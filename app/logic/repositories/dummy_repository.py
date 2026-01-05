from dataclasses import dataclass
from typing import Annotated, TypeAlias

from fastapi import Depends
from sqlalchemy import Integer, literal_column, select

from app.database import AsyncSessionDep  # noqa: TC001


@dataclass(frozen=True, kw_only=True, slots=True)
class DummyRepository:
    _session: AsyncSessionDep

    async def read_one(self) -> int:
        result = await self._session.execute(select(literal_column("1", Integer)))
        return result.scalar_one()


# FastAPI does not support the type keyword when used for dependencies
# as of October 2025 (see https://github.com/fastapi/fastapi/issues/10719):
DummyRepositoryDep: TypeAlias = Annotated[DummyRepository, Depends()]  # noqa: UP040
