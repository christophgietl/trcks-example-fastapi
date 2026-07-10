from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Iterable, Mapping, Sequence
    from decimal import Decimal
    from uuid import UUID

    from subscription_management.data_structures.domain.product import ProductStatus

type GetProductsFromDatabase = Callable[[], Awaitable[Sequence[ProductTuple]]]
type GetSubscriptionsFromDatabase = Callable[[], Awaitable[Sequence[SubscriptionTuple]]]
type GetUsersFromDatabase = Callable[[], Awaitable[Sequence[UserTuple]]]
type ProductTuple = tuple[UUID, Decimal, str, ProductStatus]
type ProductTuples = tuple[ProductTuple, ...]
type SortedById = Callable[[Iterable[StrMapping]], list[StrMapping]]
type StrMapping = Mapping[str, object]
type SubscriptionTuple = tuple[UUID, bool, UUID, UUID]
type SubscriptionTuples = tuple[SubscriptionTuple, ...]
type UserTuple = tuple[UUID, str]
type UserTuples = tuple[UserTuple, ...]
