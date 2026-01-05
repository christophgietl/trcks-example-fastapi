from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, ClassVar, Final, Literal, TypeAlias

from fastapi import Depends
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.interfaces import LoaderOption  # noqa: TC002
from trcks.oop import Wrapper

from app.data_structures.models import SubscriptionModel
from app.database import AsyncSessionDep  # noqa: TC001
from app.logic.repositories.product_repository import (
    ProductRepositoryDep,  # noqa: TC001
)
from app.logic.repositories.user_repository import UserRepositoryDep  # noqa: TC001

if TYPE_CHECKING:
    from uuid import UUID

    from trcks import AwaitableResult, Result

    from app.data_structures.domain.subscription import (
        SubscriptionWithProduct,
        SubscriptionWithUserIdAndProductId,
    )

type _BaseSubscriptionResult = Result[
    Literal["Subscription does not exist"], SubscriptionWithProduct
]
type _ProductOrUserDoesNotExist = Literal[
    "Product does not exist", "User does not exist"
]


@dataclass(frozen=True, kw_only=True, slots=True)
class SubscriptionRepository:
    _LOADER_OPTION: ClassVar[Final[LoaderOption]] = selectinload(
        SubscriptionModel.product
    )

    _product_repository: ProductRepositoryDep
    _session: AsyncSessionDep
    _user_repository: UserRepositoryDep

    def _check_that_product_and_user_exist(
        self, subscription: SubscriptionWithUserIdAndProductId
    ) -> AwaitableResult[_ProductOrUserDoesNotExist, None]:
        return (
            Wrapper(subscription)
            .tap_to_awaitable_result(
                lambda sn: self._product_repository.read_product_by_id(sn.product_id)
            )
            .tap_success_to_awaitable_result(
                lambda sn: self._user_repository.read_user_by_id(sn.user_id)
            )
            .map_success(lambda _: None)
            .core
        )

    async def _create_subscription(
        self, subscription: SubscriptionWithUserIdAndProductId
    ) -> Result[Literal["ID already exists"], None]:
        subscription_model = (
            SubscriptionModel.from_subscription_with_user_id_and_product_id(
                subscription
            )
        )
        self._session.add(subscription_model)
        try:
            await self._session.flush()
        except IntegrityError as e:
            match str(e.orig):
                case "UNIQUE constraint failed: subscription.id":
                    return "failure", "ID already exists"
                case _:  # pragma: no cover
                    raise
        else:
            return "success", None

    @staticmethod
    def _to_base_subscription_result(
        subscription_model: SubscriptionModel | None,
    ) -> _BaseSubscriptionResult:
        if subscription_model is None:
            return "failure", "Subscription does not exist"
        return "success", subscription_model.to_subscription_with_product()

    async def _update_subscription(
        self, subscription: SubscriptionWithUserIdAndProductId
    ) -> _BaseSubscriptionResult:
        updated_subscription_model = await self._session.scalar(
            update(SubscriptionModel)
            .where(SubscriptionModel.id == subscription.id)
            .values(
                is_active=subscription.is_active,
                user_id=subscription.user_id,
                product_id=subscription.product_id,
            )
            .returning(SubscriptionModel)
            .options(self._LOADER_OPTION)
        )
        return self._to_base_subscription_result(updated_subscription_model)

    def create_subscription(
        self, subscription: SubscriptionWithUserIdAndProductId
    ) -> AwaitableResult[
        Literal["ID already exists"] | _ProductOrUserDoesNotExist, None
    ]:
        return (
            Wrapper(subscription)
            # Foreign key errors from SQLite do not contain any indication
            # about which foreign key failed.
            # Therefore, we read the related entities first
            # in order to provide more specific `Failure`s:
            .tap_to_awaitable_result(self._check_that_product_and_user_exist)
            .map_success_to_awaitable_result(self._create_subscription)
            .core
        )

    async def delete_subscription(self, id_: UUID) -> _BaseSubscriptionResult:
        deleted_subscription_model = await self._session.scalar(
            delete(SubscriptionModel)
            .where(SubscriptionModel.id == id_)
            .returning(SubscriptionModel)
            .options(self._LOADER_OPTION)
        )
        return self._to_base_subscription_result(deleted_subscription_model)

    async def read_subscription_by_id(self, id_: UUID) -> _BaseSubscriptionResult:
        subscription_model = await self._session.get(
            SubscriptionModel, id_, options=[self._LOADER_OPTION]
        )
        return self._to_base_subscription_result(subscription_model)

    async def read_subscriptions(self) -> tuple[SubscriptionWithProduct, ...]:
        scalars = await self._session.scalars(
            select(SubscriptionModel).options(self._LOADER_OPTION)
        )
        subscription_models = scalars.all()
        return tuple(
            subscription_model.to_subscription_with_product()
            for subscription_model in subscription_models
        )

    def update_subscription(
        self, subscription: SubscriptionWithUserIdAndProductId
    ) -> AwaitableResult[
        Literal["Subscription does not exist"] | _ProductOrUserDoesNotExist,
        SubscriptionWithProduct,
    ]:
        return (
            Wrapper(subscription)
            # Foreign key errors from SQLite do not contain any indication
            # about which foreign key failed.
            # Therefore, we read the related entities first
            # in order to provide more specific `Failure`s:
            .tap_to_awaitable_result(self._check_that_product_and_user_exist)
            .map_success_to_awaitable_result(self._update_subscription)
            .core
        )


# FastAPI does not support the type keyword when used for dependencies
# as of October 2025 (see https://github.com/fastapi/fastapi/issues/10719):
SubscriptionRepositoryDep: TypeAlias = Annotated[SubscriptionRepository, Depends()]  # noqa: UP040
