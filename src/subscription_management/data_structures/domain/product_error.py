import dataclasses
from typing import TYPE_CHECKING, Literal, final

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
class ProductInDeprecatedStatusError(_ProductErrorWithId):
    pass


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ProductInDraftStatusError(_ProductErrorWithId):
    pass


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ProductPayloadUpdateError:
    reason: Literal[
        "Cannot modify non-status attributes of a deprecated product",
        "Cannot modify non-status attributes of a published product",
    ]
    status: ProductStatus


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ProductStatusDeprecatedError(_ProductErrorWithId):
    pass


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ProductStatusPublishedError(_ProductErrorWithId):
    pass


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ProductStatusUpdateError:
    reason: Literal[
        "Cannot change status from deprecated to draft",
        "Cannot change status from deprecated to published",
        "Cannot change status from published to draft",
    ]
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
