from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, ClassVar, Final, final

from fastapi import Depends
from sqlalchemy import delete, insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from trcks.oop import AwaitableTupleWrapper, Wrapper

from subscription_management.data_structures.domain.user import (
    UserWithSubscriptionsWithProducts,
)
from subscription_management.data_structures.domain.user_error import (
    UserWithEmailAlreadyExistsError,
    UserWithEmailDoesNotExistError,
    UserWithIdAlreadyExistsError,
    UserWithIdDoesNotExistError,
)
from subscription_management.data_structures.models import SubscriptionModel, UserModel
from subscription_management.logic.database import AsyncSessionDep  # noqa: TC001

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm.interfaces import LoaderOption
    from trcks import AwaitableResult, AwaitableTuple, Result

    from subscription_management.data_structures.domain.user import User

type _UserByIdResult = Result[
    UserWithIdDoesNotExistError, UserWithSubscriptionsWithProducts
]
type _UserByEmailResult = Result[
    UserWithEmailDoesNotExistError, UserWithSubscriptionsWithProducts
]

type UserRepositoryDep = Annotated[UserRepository, Depends()]


@final
@dataclass(frozen=True, kw_only=True, slots=True)
class UserRepository:
    _LOADER_OPTION: ClassVar[Final[LoaderOption]] = selectinload(
        UserModel.subscriptions
    ).selectinload(SubscriptionModel.product)

    _session: AsyncSessionDep

    async def _create_user_model(
        self, user: User
    ) -> Result[
        UserWithEmailAlreadyExistsError | UserWithIdAlreadyExistsError,
        UserModel,
    ]:
        statement = (
            insert(UserModel)
            .values(id=user.id, email=user.email)
            .returning(UserModel)
            .options(self._LOADER_OPTION)
        )
        try:
            scalars = await self._session.scalars(statement=statement)
        except IntegrityError as e:
            match str(e.orig):
                case "UNIQUE constraint failed: user.id":
                    return "failure", UserWithIdAlreadyExistsError(id=user.id)
                case "UNIQUE constraint failed: user.email":
                    return "failure", UserWithEmailAlreadyExistsError(email=user.email)
                case _:  # pragma: no cover
                    raise
        else:
            return "success", scalars.one()

    async def _read_user_models(self) -> tuple[UserModel, ...]:
        statement = select(UserModel).options(self._LOADER_OPTION)
        scalars = await self._session.scalars(statement=statement)
        return tuple(scalars.all())

    def create_user(
        self, user: User
    ) -> AwaitableResult[
        UserWithEmailAlreadyExistsError | UserWithIdAlreadyExistsError,
        UserWithSubscriptionsWithProducts,
    ]:
        return (
            Wrapper(user)
            .map_to_awaitable_result(self._create_user_model)
            .map_success(UserModel.to_user_with_subscriptions_with_products)
            .core
        )

    async def delete_user(self, id_: UUID) -> _UserByIdResult:
        statement = (
            delete(UserModel)
            .where(UserModel.id == id_)
            .returning(UserModel)
            .options(self._LOADER_OPTION)
        )
        user_model = await self._session.scalar(statement=statement)
        if user_model is None:
            return "failure", UserWithIdDoesNotExistError(id=id_)
        return "success", user_model.to_user_with_subscriptions_with_products()

    async def read_user_by_email(self, email: str) -> _UserByEmailResult:
        statement = (
            select(UserModel)
            .where(UserModel.email == email)
            .options(self._LOADER_OPTION)
        )
        user_model = await self._session.scalar(statement=statement)
        if user_model is None:
            return "failure", UserWithEmailDoesNotExistError(email=email)
        return "success", user_model.to_user_with_subscriptions_with_products()

    async def read_user_by_id(self, id_: UUID) -> _UserByIdResult:
        user_model = await self._session.get(
            UserModel,
            id_,
            options=(self._LOADER_OPTION,),
        )
        if user_model is None:
            return "failure", UserWithIdDoesNotExistError(id=id_)
        return "success", user_model.to_user_with_subscriptions_with_products()

    def read_users(self) -> AwaitableTuple[UserWithSubscriptionsWithProducts]:
        return (
            AwaitableTupleWrapper(self._read_user_models())
            .map(UserModel.to_user_with_subscriptions_with_products)
            .core
        )

    async def update_user(
        self, user: User
    ) -> Result[
        UserWithIdDoesNotExistError | UserWithEmailAlreadyExistsError,
        UserWithSubscriptionsWithProducts,
    ]:
        statement = (
            update(UserModel)
            .where(UserModel.id == user.id)
            .values(email=user.email)
            .returning(UserModel)
            .options(self._LOADER_OPTION)
        )
        try:
            updated_user_model = await self._session.scalar(statement=statement)
        except IntegrityError as e:
            match str(e.orig):
                case "UNIQUE constraint failed: user.email":
                    return "failure", UserWithEmailAlreadyExistsError(email=user.email)
                case _:  # pragma: no cover
                    raise
        else:
            if updated_user_model is None:
                return "failure", UserWithIdDoesNotExistError(id=user.id)
            return (
                "success",
                updated_user_model.to_user_with_subscriptions_with_products(),
            )
