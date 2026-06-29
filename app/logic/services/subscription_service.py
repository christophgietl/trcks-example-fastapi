from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, Literal, assert_never, final

from fastapi import Depends
from trcks.oop import Wrapper

from app.logic.repositories.product_repository import (
    ProductRepositoryDep,  # noqa: TC001
)
from app.logic.repositories.subscription_repository import (
    SubscriptionRepositoryDep,  # noqa: TC001
)

if TYPE_CHECKING:
    from uuid import UUID

    from trcks import AwaitableResult, AwaitableTuple, Result

    from app.data_structures.domain.product import Product
    from app.data_structures.domain.subscription import (
        SubscriptionWithProduct,
        SubscriptionWithUserIdAndProductId,
    )

type _AwaitableReadSubscriptionResult = AwaitableResult[
    _SubscriptionDoesNotExistLiteral, SubscriptionWithProduct
]
type _ProductNotSubscribableLiteral = (
    Literal["Product does not exist"] | _ProductStatusLiteral
)
type _ProductStatusLiteral = Literal[
    "Product is in draft status", "Product is in deprecated status"
]
type _SubscriptionDoesNotExistLiteral = Literal["Subscription does not exist"]
type _UserDoesNotExistLiteral = Literal["User does not exist"]

type SubscriptionServiceDep = Annotated[SubscriptionService, Depends()]


@final
@dataclass(frozen=True, kw_only=True, slots=True)
class SubscriptionService:
    _product_repository: ProductRepositoryDep
    _subscription_repository: SubscriptionRepositoryDep

    @staticmethod
    def _check_product_status(product: Product) -> Result[_ProductStatusLiteral, None]:
        match product.status:
            case "draft":
                return "failure", "Product is in draft status"
            case "published":
                return "success", None
            case "deprecated":
                return "failure", "Product is in deprecated status"
            case _:  # pragma: no cover
                assert_never(product.status)

    def _read_product_and_check_status(
        self, subscription: SubscriptionWithUserIdAndProductId
    ) -> AwaitableResult[_ProductNotSubscribableLiteral, None]:
        return (
            Wrapper(subscription.product_id)
            .map_to_awaitable_result(self._product_repository.read_product_by_id)
            .map_success_to_result(self._check_product_status)
            .core
        )

    def create_subscription(
        self, subscription: SubscriptionWithUserIdAndProductId
    ) -> AwaitableResult[
        Literal["ID already exists"]
        | _ProductNotSubscribableLiteral
        | _UserDoesNotExistLiteral,
        None,
    ]:
        return (
            Wrapper(subscription)
            .tap_to_awaitable_result(self._read_product_and_check_status)
            .map_success_to_awaitable_result(
                self._subscription_repository.create_subscription
            )
            .core
        )

    def delete_subscription(self, id_: UUID) -> _AwaitableReadSubscriptionResult:
        return self._subscription_repository.delete_subscription(id_)

    def read_subscription_by_id(self, id_: UUID) -> _AwaitableReadSubscriptionResult:
        return self._subscription_repository.read_subscription_by_id(id_)

    def read_subscriptions(self) -> AwaitableTuple[SubscriptionWithProduct]:
        return self._subscription_repository.read_subscriptions()

    def update_subscription(
        self, subscription: SubscriptionWithUserIdAndProductId
    ) -> AwaitableResult[
        _ProductNotSubscribableLiteral
        | _SubscriptionDoesNotExistLiteral
        | _UserDoesNotExistLiteral,
        SubscriptionWithProduct,
    ]:
        return (
            Wrapper(subscription)
            .tap_to_awaitable_result(self._read_product_and_check_status)
            .map_success_to_awaitable_result(
                self._subscription_repository.update_subscription
            )
            .core
        )
