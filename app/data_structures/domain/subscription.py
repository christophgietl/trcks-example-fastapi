import dataclasses
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

    from app.data_structures.domain.product import Product


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class _Subscription:
    id: UUID
    is_active: bool


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class SubscriptionWithProduct(_Subscription):
    product: Product


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class SubscriptionWithUserIdAndProductId(_Subscription):
    user_id: UUID
    product_id: UUID
