import dataclasses
from typing import TYPE_CHECKING, final

if TYPE_CHECKING:
    from uuid import UUID

    from subscription_management.data_structures.domain.product import ProductStatus


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class _ProductErrorWithId:
    id: UUID


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class _ProductErrorWithName:
    name: str


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ProductNotDeletableBecauseDeprecatedError(_ProductErrorWithId):
    pass


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ProductNotDeletableBecausePublishedError(_ProductErrorWithId):
    pass


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ProductNotSubscribableBecauseDeprecatedError(_ProductErrorWithId):
    pass


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ProductNotSubscribableBecauseDraftError(_ProductErrorWithId):
    pass


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ProductPayloadNotUpdatableBecauseStatusError:
    status: ProductStatus


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ProductStatusTransitionNotAllowedError:
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
