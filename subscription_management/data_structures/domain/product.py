import dataclasses
from typing import TYPE_CHECKING, Literal, final

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
class ProductDoesNotExistError:
    reason: Literal["Product does not exist"] = "Product does not exist"
    id: UUID | None = None
    name: str | None = None


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ProductIdAlreadyExistsError:
    reason: Literal["ID already exists"] = "ID already exists"
    id: UUID


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ProductInDeprecatedStatusError:
    reason: Literal["Product is in deprecated status"] = (
        "Product is in deprecated status"
    )
    id: UUID | None = None


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ProductInDraftStatusError:
    reason: Literal["Product is in draft status"] = "Product is in draft status"
    id: UUID | None = None


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ProductNameAlreadyExistsError:
    reason: Literal["Name already exists"] = "Name already exists"
    name: str


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ProductPayloadUpdateError:
    reason: _ProductPayloadUpdateErrorReason
    status: ProductStatus


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ProductStatusDeprecatedError:
    reason: Literal["Product status is deprecated"] = "Product status is deprecated"
    id: UUID | None = None


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ProductStatusPublishedError:
    reason: Literal["Product status is published"] = "Product status is published"
    id: UUID | None = None


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ProductStatusUpdateError:
    reason: _ProductStatusUpdateErrorReason
    before: ProductStatus
    after: ProductStatus
