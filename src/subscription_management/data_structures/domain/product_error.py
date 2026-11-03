import dataclasses
from typing import TYPE_CHECKING, Literal, final

from subscription_management.data_structures.domain.product import (  # noqa: TC001
    ProductStatus,
)

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
    status: Literal[ProductStatus.PUBLISHED, ProductStatus.DEPRECATED]


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ProductNotSubscribableBecauseStatusError(_ProductErrorWithId):
    status: Literal[ProductStatus.DRAFT, ProductStatus.DEPRECATED]


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ProductPayloadNotUpdatableBecauseStatusError(_ProductErrorWithId):
    status: Literal[ProductStatus.PUBLISHED, ProductStatus.DEPRECATED]


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ProductStatusTransitionNotAllowedError(_ProductErrorWithId):
    before: ProductStatus
    after: ProductStatus


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
