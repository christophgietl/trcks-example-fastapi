import dataclasses
from typing import TYPE_CHECKING, Literal, final

if TYPE_CHECKING:
    from uuid import UUID

    from subscription_management.data_structures.domain.product import ProductStatus


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class Error:
    reason: str


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


type _SubscriptionErrorReason = Literal[
    "ID already exists", "Subscription does not exist"
]


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class SubscriptionError(Error):
    reason: _SubscriptionErrorReason


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class SubscriptionDoesNotExistError(SubscriptionError):
    reason: Literal["Subscription does not exist"] = "Subscription does not exist"
    id: UUID | None = None


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class SubscriptionIdAlreadyExistsError(SubscriptionError):
    reason: Literal["ID already exists"] = "ID already exists"
    id: UUID


type _UserErrorReason = Literal[
    "Email already exists", "ID already exists", "User does not exist"
]


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class UserError(Error):
    reason: _UserErrorReason


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class UserDoesNotExistError(UserError):
    reason: Literal["User does not exist"] = "User does not exist"
    id: UUID | None = None
    email: str | None = None


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class UserEmailAlreadyExistsError(UserError):
    reason: Literal["Email already exists"] = "Email already exists"
    email: str


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class UserIdAlreadyExistsError(UserError):
    reason: Literal["ID already exists"] = "ID already exists"
    id: UUID
