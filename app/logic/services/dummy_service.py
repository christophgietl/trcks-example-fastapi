from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, TypeAlias

from fastapi import Depends

from app.logic.repositories.dummy_repository import DummyRepositoryDep  # noqa: TC001

if TYPE_CHECKING:
    from collections.abc import Awaitable


@dataclass(frozen=True, kw_only=True, slots=True)
class DummyService:
    _dummy_repository: DummyRepositoryDep

    def read_one(self) -> Awaitable[int]:
        return self._dummy_repository.read_one()


# FastAPI does not support the type keyword when used for dependencies
# as of October 2025 (see https://github.com/fastapi/fastapi/issues/10719):
DummyServiceDep: TypeAlias = Annotated[DummyService, Depends()]  # noqa: UP040
