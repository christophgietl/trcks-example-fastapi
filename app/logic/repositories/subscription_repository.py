from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, ClassVar, Final, Literal, final

from fastapi import Depends
from sqlalchemy import delete, insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from trcks.oop import AwaitableTupleWrapper, Wrapper

from app.data_structures.models import SubscriptionModel
from app.database import AsyncSessionDep  # noqa: TC001
from app.logic.repositories.product_repository import (
    ProductRepositoryDep,  # noqa: TC001
)
from app.logic.repositories.user_repository import UserRepositoryDep  # noqa: TC001

if TYPE_CHECKING:
    from collections.abc import Awaitable
    from uuid import UUID

    from sqlalchemy.orm.interfaces import LoaderOption
    from trcks import AwaitableResult, AwaitableTuple, Result

    from app.data_structures.domain.subscription import (
        SubscriptionWithProduct,
        SubscriptionWithUserIdAndProductId,
    )

type _AwaitableBaseSubscriptionResult = Awaitable[_BaseSubscriptionResult]
type _BaseSubscriptionResult = Result[
    Literal["Subscription does not exist"], SubscriptionWithProduct
]
type _ProductOrUserDoesNotExist = Literal[
    "Product does not exist", "User does not exist"
]

type SubscriptionRepositoryDep = Annotated[SubscriptionRepository, Depends()]


@final
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

    async def _create_subscription_model(
        self, subscription: SubscriptionWithUserIdAndProductId
    ) -> Result[Literal["ID already exists"], SubscriptionModel]:
        statement = (
            insert(SubscriptionModel)
            .values(
                id=subscription.id,
                is_active=subscription.is_active,
                user_id=subscription.user_id,
                product_id=subscription.product_id,
            )
            .returning(SubscriptionModel)
            .options(self._LOADER_OPTION)
        )
        try:
            scalars = await self._session.scalars(statement=statement)
        except IntegrityError as e:
            match str(e.orig):
                case "UNIQUE constraint failed: subscription.id":
                    return "failure", "ID already exists"
                case _:  # pragma: no cover
                    raise
        else:
            return "success", scalars.one()

    async def _delete_subscription_model(self, id_: UUID) -> SubscriptionModel | None:
        statement = (
            delete(SubscriptionModel)
            .where(SubscriptionModel.id == id_)
            .returning(SubscriptionModel)
            .options(self._LOADER_OPTION)
        )
        return await self._session.scalar(statement=statement)

    async def _read_subscription_model_by_id(
        self, id_: UUID
    ) -> SubscriptionModel | None:
        return await self._session.get(
            SubscriptionModel, id_, options=[self._LOADER_OPTION]
        )

    async def _read_subscription_models(self) -> tuple[SubscriptionModel, ...]:
        statement = select(SubscriptionModel).options(self._LOADER_OPTION)
        scalars = await self._session.scalars(statement=statement)
        return tuple(scalars.all())

    @staticmethod
    def _to_base_subscription_result(
        subscription_model: SubscriptionModel | None,
    ) -> _BaseSubscriptionResult:
        if subscription_model is None:
            return "failure", "Subscription does not exist"
        return "success", subscription_model.to_subscription_with_product()

    async def _update_subscription_model(
        self, subscription: SubscriptionWithUserIdAndProductId
    ) -> SubscriptionModel | None:
        statement = (
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
        return await self._session.scalar(statement=statement)

    def create_subscription(
        self, subscription: SubscriptionWithUserIdAndProductId
    ) -> AwaitableResult[
        Literal["ID already exists"] | _ProductOrUserDoesNotExist,
        SubscriptionWithProduct,
    ]:
        return (
            Wrapper(subscription)
            # Foreign key errors from SQLite do not contain any indication
            # about which foreign key failed.
            # Therefore, we read the related entities first
            # in order to provide more specific `Failure`s:
            .tap_to_awaitable_result(self._check_that_product_and_user_exist)
            .map_success_to_awaitable_result(self._create_subscription_model)
            .map_success(SubscriptionModel.to_subscription_with_product)
            .core
        )

    def delete_subscription(self, id_: UUID) -> _AwaitableBaseSubscriptionResult:
        return (
            Wrapper(id_)
            .map_to_awaitable(self._delete_subscription_model)
            .map(self._to_base_subscription_result)
            .core
        )

    def read_subscription_by_id(self, id_: UUID) -> _AwaitableBaseSubscriptionResult:
        return (
            Wrapper(id_)
            .map_to_awaitable(self._read_subscription_model_by_id)
            .map(self._to_base_subscription_result)
            .core
        )

    def read_subscriptions(self) -> AwaitableTuple[SubscriptionWithProduct]:
        return (
            AwaitableTupleWrapper(self._read_subscription_models())
            .map(SubscriptionModel.to_subscription_with_product)
            .core
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
            .map_success_to_awaitable(self._update_subscription_model)
            .map_success_to_result(self._to_base_subscription_result)
            .core
        )
