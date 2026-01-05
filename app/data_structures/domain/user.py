import dataclasses
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

    from app.data_structures.domain.subscription import SubscriptionWithProduct


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class User:
    id: UUID
    email: str


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class UserWithSubscriptionsWithProducts(User):
    subscriptions_with_products: tuple[SubscriptionWithProduct, ...]
