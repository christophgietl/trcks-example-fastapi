import dataclasses
from typing import TYPE_CHECKING, Literal, final

from subscription_management.data_structures.domain.errors import Error

if TYPE_CHECKING:
    from decimal import Decimal
    from uuid import UUID

type ProductStatus = Literal["draft", "published", "deprecated"]


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class Product:
    id: UUID
    monthly_fee_in_euros: Decimal
    name: str
    status: ProductStatus


type _ProductErrorReason = Literal[
    "Cannot change status from deprecated to draft",
    "Cannot change status from deprecated to published",
    "Cannot change status from published to draft",
    "Cannot modify non-status attributes of a deprecated product",
    "Cannot modify non-status attributes of a published product",
    "ID already exists",
    "Name already exists",
    "Product does not exist",
    "Product is in deprecated status",
    "Product is in draft status",
    "Product status is deprecated",
    "Product status is published",
]


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ProductError(Error):
    reason: _ProductErrorReason


type _ProductPayloadUpdateErrorReason = Literal[
    "Cannot modify non-status attributes of a deprecated product",
    "Cannot modify non-status attributes of a published product",
]

type _ProductStatusUpdateErrorReason = Literal[
    "Cannot change status from deprecated to draft",
    "Cannot change status from deprecated to published",
    "Cannot change status from published to draft",
]


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ProductDoesNotExistError(ProductError):
    reason: Literal["Product does not exist"] = "Product does not exist"
    id: UUID | None = None
    name: str | None = None


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ProductIdAlreadyExistsError(ProductError):
    reason: Literal["ID already exists"] = "ID already exists"
    id: UUID


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ProductInDeprecatedStatusError(ProductError):
    reason: Literal["Product is in deprecated status"] = (
        "Product is in deprecated status"
    )
    id: UUID | None = None


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ProductInDraftStatusError(ProductError):
    reason: Literal["Product is in draft status"] = "Product is in draft status"
    id: UUID | None = None


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ProductNameAlreadyExistsError(ProductError):
    reason: Literal["Name already exists"] = "Name already exists"
    name: str


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ProductPayloadUpdateError(ProductError):
    reason: _ProductPayloadUpdateErrorReason
    status: ProductStatus


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ProductStatusDeprecatedError(ProductError):
    reason: Literal["Product status is deprecated"] = "Product status is deprecated"
    id: UUID | None = None


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ProductStatusPublishedError(ProductError):
    reason: Literal["Product status is published"] = "Product status is published"
    id: UUID | None = None


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ProductStatusUpdateError(ProductError):
    reason: _ProductStatusUpdateErrorReason
    before: ProductStatus
    after: ProductStatus
