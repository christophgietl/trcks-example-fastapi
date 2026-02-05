from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, Literal, assert_never

from fastapi import Depends
from trcks.oop import Wrapper

from app.logic.repositories.product_repository import (
    ProductRepositoryDep,  # noqa: TC001
)
from app.logic.repositories.subscription_repository import (
    SubscriptionRepositoryDep,  # noqa: TC001
)

if TYPE_CHECKING:
    from collections.abc import Awaitable
    from uuid import UUID

    from trcks import AwaitableResult, Result

    from app.data_structures.domain.product import Product
    from app.data_structures.domain.subscription import (
        SubscriptionWithProduct,
        SubscriptionWithUserIdAndProductId,
    )

type _ProductStatusLiteral = Literal[
    "Product is in draft status", "Product is in deprecated status"
]

type SubscriptionServiceDep = Annotated[SubscriptionService, Depends()]


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
    ) -> AwaitableResult[
        Literal["Product does not exist"] | _ProductStatusLiteral, None
    ]:
        return (
            Wrapper(subscription.product_id)
            .map_to_awaitable_result(self._product_repository.read_product_by_id)
            .map_success_to_result(self._check_product_status)
            .core
        )

    def create_subscription(
        self, subscription: SubscriptionWithUserIdAndProductId
    ) -> AwaitableResult[
        Literal["ID already exists", "User does not exist", "Product does not exist"]
        | _ProductStatusLiteral,
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

    def delete_subscription(
        self, id_: UUID
    ) -> AwaitableResult[
        Literal["Subscription does not exist"], SubscriptionWithProduct
    ]:
        return self._subscription_repository.delete_subscription(id_)

    def read_subscription_by_id(
        self, id_: UUID
    ) -> AwaitableResult[
        Literal["Subscription does not exist"], SubscriptionWithProduct
    ]:
        return self._subscription_repository.read_subscription_by_id(id_)

    def read_subscriptions(self) -> Awaitable[tuple[SubscriptionWithProduct, ...]]:
        return self._subscription_repository.read_subscriptions()

    def update_subscription(
        self, subscription: SubscriptionWithUserIdAndProductId
    ) -> AwaitableResult[
        Literal[
            "Subscription does not exist",
            "User does not exist",
            "Product does not exist",
        ]
        | _ProductStatusLiteral,
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
