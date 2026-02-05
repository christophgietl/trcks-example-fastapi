from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends
from sqlalchemy import Integer, literal_column, select

from app.database import AsyncSessionDep  # noqa: TC001

type DummyRepositoryDep = Annotated[DummyRepository, Depends()]


@dataclass(frozen=True, kw_only=True, slots=True)
class DummyRepository:
    _session: AsyncSessionDep

    async def read_one(self) -> int:
        result = await self._session.execute(select(literal_column("1", Integer)))
        return result.scalar_one()
