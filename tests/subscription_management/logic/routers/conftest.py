import functools
from collections.abc import Awaitable, Callable, Iterable, Mapping, Sequence
from typing import TYPE_CHECKING, Any, Protocol

import pytest

if TYPE_CHECKING:
    from sqlalchemy import Select
    from sqlalchemy.ext.asyncio import AsyncSession


type AddToDatabase = Callable[[*tuple[object, ...]], Awaitable[None]]
type AnyTuple = tuple[Any, ...]
type StrMapping = Mapping[str, object]


class GetFromDatabase(Protocol):
    def __call__[TP: AnyTuple](
        self, statement: Select[TP]
    ) -> Awaitable[Sequence[TP]]: ...


def _get_id(d: StrMapping) -> str:
    return str(d["id"])


async def _add_to_database(session: AsyncSession, *instances: object) -> None:
    async with session.begin():
        session.add_all(instances)


async def _get_from_database[TP: AnyTuple](
    session: AsyncSession, statement: Select[TP]
) -> Sequence[TP]:
    async with session.begin():
        result = await session.execute(statement)
        return result.tuples().all()


def _sorted_by_id(ds: Iterable[StrMapping]) -> list[StrMapping]:
    return sorted(ds, key=_get_id)


@pytest.fixture
def add_to_database(session: AsyncSession) -> AddToDatabase:
    return functools.partial(_add_to_database, session)


@pytest.fixture
def get_from_database(session: AsyncSession) -> GetFromDatabase:
    return functools.partial(_get_from_database, session)


@pytest.fixture
def sorted_by_id() -> Callable[[Iterable[StrMapping]], list[StrMapping]]:
    return _sorted_by_id
