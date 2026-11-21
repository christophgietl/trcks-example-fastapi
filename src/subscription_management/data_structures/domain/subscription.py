import dataclasses
from typing import TYPE_CHECKING, final

if TYPE_CHECKING:
    from uuid import UUID

    from subscription_management.data_structures.domain.do_not_update import (
        DO_NOT_UPDATE,
    )
    from subscription_management.data_structures.domain.product import Product


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class _Subscription:
    id: UUID
    is_active: bool


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class SubscriptionUpdate:
    id: UUID
    is_active: bool | DO_NOT_UPDATE
    user_id: UUID | DO_NOT_UPDATE
    product_id: UUID | DO_NOT_UPDATE


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class SubscriptionWithProduct(_Subscription):
    product: Product


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class SubscriptionWithUserIdAndProductId(_Subscription):
    user_id: UUID
    product_id: UUID
