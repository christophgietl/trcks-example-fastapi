import dataclasses
from typing import TYPE_CHECKING, Literal, final

if TYPE_CHECKING:
    from uuid import UUID


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class _ProductErrorWithId:
    id: UUID


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class _ProductErrorWithName:
    name: str


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ProductNotDeletableBecauseStatusError(_ProductErrorWithId):
    status: Literal["published", "deprecated"]


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ProductNotSubscribableBecauseStatusError(_ProductErrorWithId):
    status: Literal["draft", "deprecated"]


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ProductPayloadNotUpdatableBecauseStatusError:
    status: Literal["published", "deprecated"]


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ProductStatusTransitionNotAllowedError:
    before: Literal["published", "deprecated"]
    after: Literal["draft", "published"]


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ProductWithIdAlreadyExistsError(_ProductErrorWithId):
    pass


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ProductWithIdDoesNotExistError(_ProductErrorWithId):
    pass


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ProductWithNameAlreadyExistsError(_ProductErrorWithName):
    pass


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ProductWithNameDoesNotExistError(_ProductErrorWithName):
    pass
