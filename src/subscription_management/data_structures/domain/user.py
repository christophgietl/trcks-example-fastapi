import dataclasses
from typing import TYPE_CHECKING, final

if TYPE_CHECKING:
    from uuid import UUID

    from subscription_management.data_structures.domain.do_not_update import (
        DO_NOT_UPDATE,
    )
    from subscription_management.data_structures.domain.subscription import (
        SubscriptionWithProduct,
    )


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class _User:
    id: UUID
    email: str | DO_NOT_UPDATE


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class _UserWithRequiredEmail(_User):
    email: str


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class User(_UserWithRequiredEmail):
    pass


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class UserUpdate(_User):
    pass


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class UserWithSubscriptionsWithProducts(_UserWithRequiredEmail):
    subscriptions_with_products: tuple[SubscriptionWithProduct, ...]
