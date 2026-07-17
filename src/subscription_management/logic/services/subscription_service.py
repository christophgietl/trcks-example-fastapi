from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, assert_never, final

from fastapi import Depends
from trcks.oop import Wrapper

from subscription_management.data_structures.domain.product_error import (
    ProductNotSubscribableBecauseStatusError,
    ProductWithIdDoesNotExistError,
)
from subscription_management.logic.repositories.product_repository import (
    ProductRepositoryDep,  # noqa: TC001
)
from subscription_management.logic.repositories.subscription_repository import (
    SubscriptionRepositoryDep,  # noqa: TC001
)

if TYPE_CHECKING:
    from uuid import UUID

    from trcks import AwaitableResult, AwaitableTuple, Result

    from subscription_management.data_structures.domain.product import Product
    from subscription_management.data_structures.domain.subscription import (
        SubscriptionWithProduct,
        SubscriptionWithUserIdAndProductId,
    )
    from subscription_management.data_structures.domain.subscription_error import (
        SubscriptionWithIdAlreadyExistsError,
        SubscriptionWithIdDoesNotExistError,
    )
    from subscription_management.data_structures.domain.user_error import (
        UserWithIdDoesNotExistError,
    )

type _ProductNotSubscribableError = (
    ProductNotSubscribableBecauseStatusError | ProductWithIdDoesNotExistError
)

type SubscriptionServiceDep = Annotated[SubscriptionService, Depends()]


@final
@dataclass(frozen=True, kw_only=True, slots=True)
class SubscriptionService:
    _product_repository: ProductRepositoryDep
    _subscription_repository: SubscriptionRepositoryDep

    @staticmethod
    def _check_product_status(
        product: Product,
    ) -> Result[ProductNotSubscribableBecauseStatusError, None]:
        match product.status:
            case "draft" | "deprecated":
                return "failure", ProductNotSubscribableBecauseStatusError(
                    id=product.id, status=product.status
                )
            case "published":
                return "success", None
            case _:  # pragma: no cover
                assert_never(product.status)  # pyright: ignore[reportUnreachable]

    def _read_product_and_check_status(
        self, subscription: SubscriptionWithUserIdAndProductId
    ) -> AwaitableResult[_ProductNotSubscribableError, None]:
        return (
            Wrapper(subscription.product_id)
            .map_to_awaitable_result(self._product_repository.read_product_by_id)
            .map_success_to_result(self._check_product_status)
            .core
        )

    def create_subscription(
        self, subscription: SubscriptionWithUserIdAndProductId
    ) -> AwaitableResult[
        _ProductNotSubscribableError
        | SubscriptionWithIdAlreadyExistsError
        | UserWithIdDoesNotExistError,
        SubscriptionWithProduct,
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
    ) -> AwaitableResult[SubscriptionWithIdDoesNotExistError, SubscriptionWithProduct]:
        return self._subscription_repository.delete_subscription(id_)

    def read_subscription_by_id(
        self, id_: UUID
    ) -> AwaitableResult[SubscriptionWithIdDoesNotExistError, SubscriptionWithProduct]:
        return self._subscription_repository.read_subscription_by_id(id_)

    def read_subscriptions(self) -> AwaitableTuple[SubscriptionWithProduct]:
        return self._subscription_repository.read_subscriptions()

    def update_subscription(
        self, subscription: SubscriptionWithUserIdAndProductId
    ) -> AwaitableResult[
        _ProductNotSubscribableError
        | SubscriptionWithIdDoesNotExistError
        | UserWithIdDoesNotExistError,
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
