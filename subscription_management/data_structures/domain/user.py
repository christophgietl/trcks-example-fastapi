import dataclasses
from typing import TYPE_CHECKING, Literal, final

from subscription_management.data_structures.domain.errors import Error

if TYPE_CHECKING:
    from uuid import UUID

    from subscription_management.data_structures.domain.subscription import (
        SubscriptionWithProduct,
    )


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class _User:
    id: UUID
    email: str


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class User(_User):
    pass


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class UserWithSubscriptionsWithProducts(_User):
    subscriptions_with_products: tuple[SubscriptionWithProduct, ...]


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
