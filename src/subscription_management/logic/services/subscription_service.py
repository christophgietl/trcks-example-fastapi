from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, assert_never, final

from fastapi import Depends
from trcks.oop import Wrapper

from subscription_management.data_structures.domain.do_not_update import (
    DO_NOT_UPDATE,
)
from subscription_management.data_structures.domain.product_error import (
    ProductNotSubscribableBecauseStatusError,
    ProductWithIdDoesNotExistError,
)
from subscription_management.data_structures.domain.subscription import (
    SubscriptionWithUserIdAndProductId,
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
        SubscriptionUpdate,
        SubscriptionWithProduct,
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

    def _add_old_subscription(
        self, subscription_update: SubscriptionUpdate
    ) -> AwaitableResult[
        SubscriptionWithIdDoesNotExistError, SubscriptionWithUserIdAndProductId
    ]:
        return (
            Wrapper(subscription_update.id)
            .map_to_awaitable_result(
                self._subscription_repository.read_subscription_with_user_id_and_product_id_by_id
            )
            .map_success(
                self._merge_subscription_update,
                subscription_update=subscription_update,
            )
            .core
        )

    @staticmethod
    def _ensure_product_status_is_published(
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

    @staticmethod
    def _merge_subscription_update(
        before: SubscriptionWithUserIdAndProductId,
        subscription_update: SubscriptionUpdate,
    ) -> SubscriptionWithUserIdAndProductId:
        return SubscriptionWithUserIdAndProductId(
            id=before.id,
            is_active=(
                subscription_update.is_active
                if subscription_update.is_active is not DO_NOT_UPDATE
                else before.is_active
            ),
            user_id=(
                subscription_update.user_id
                if subscription_update.user_id is not DO_NOT_UPDATE
                else before.user_id
            ),
            product_id=(
                subscription_update.product_id
                if subscription_update.product_id is not DO_NOT_UPDATE
                else before.product_id
            ),
        )

    def _read_product_and_ensure_status_is_published(
        self, subscription: SubscriptionWithUserIdAndProductId
    ) -> AwaitableResult[_ProductNotSubscribableError, None]:
        return (
            Wrapper(subscription.product_id)
            .map_to_awaitable_result(self._product_repository.read_product_by_id)
            .map_success_to_result(self._ensure_product_status_is_published)
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
            .tap_to_awaitable_result(self._read_product_and_ensure_status_is_published)
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
        self, subscription_update: SubscriptionUpdate
    ) -> AwaitableResult[
        _ProductNotSubscribableError
        | SubscriptionWithIdDoesNotExistError
        | UserWithIdDoesNotExistError,
        SubscriptionWithProduct,
    ]:
        return (
            Wrapper(subscription_update)
            .map_to_awaitable_result(self._add_old_subscription)
            .tap_success_to_awaitable_result(
                self._read_product_and_ensure_status_is_published
            )
            .map_success_to_awaitable_result(
                self._subscription_repository.update_subscription
            )
            .core
        )
