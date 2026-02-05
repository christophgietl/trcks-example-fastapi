from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated

from fastapi import Depends

from app.logic.repositories.dummy_repository import DummyRepositoryDep  # noqa: TC001

if TYPE_CHECKING:
    from collections.abc import Awaitable

type DummyServiceDep = Annotated[DummyService, Depends()]


@dataclass(frozen=True, kw_only=True, slots=True)
class DummyService:
    _dummy_repository: DummyRepositoryDep

    def read_one(self) -> Awaitable[int]:
        return self._dummy_repository.read_one()
