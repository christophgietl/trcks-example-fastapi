import dataclasses
from typing import TYPE_CHECKING, Literal, final

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


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class UserDoesNotExistError:
    reason: Literal["User does not exist"] = "User does not exist"
    id: UUID | None = None
    email: str | None = None


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class UserEmailAlreadyExistsError:
    reason: Literal["Email already exists"] = "Email already exists"
    email: str


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class UserIdAlreadyExistsError:
    reason: Literal["ID already exists"] = "ID already exists"
    id: UUID
