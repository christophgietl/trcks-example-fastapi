from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, ClassVar, Final, final

from fastapi import Depends
from sqlalchemy import delete, insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from trcks.oop import AwaitableTupleWrapper, Wrapper

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

    from subscription_management.data_structures.domain.user import (
        User,
        UserWithSubscriptionsWithProducts,
    )

type _CreateUserError = UserWithEmailAlreadyExistsError | UserWithIdAlreadyExistsError
type _UpdateUserError = UserWithEmailAlreadyExistsError | UserWithIdDoesNotExistError

type UserRepositoryDep = Annotated[UserRepository, Depends()]


@final
@dataclass(frozen=True, kw_only=True, slots=True)
class UserRepository:
    _LOADER_OPTION: ClassVar[Final[LoaderOption]] = selectinload(
        UserModel.subscriptions
    ).selectinload(SubscriptionModel.product)

    _session: AsyncSessionDep

    async def _create_user(self, user: User) -> Result[_CreateUserError, UserModel]:
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

    async def _delete_user(
        self, id_: UUID
    ) -> Result[UserWithIdDoesNotExistError, UserModel]:
        statement = (
            delete(UserModel)
            .where(UserModel.id == id_)
            .returning(UserModel)
            .options(self._LOADER_OPTION)
        )
        user_model = await self._session.scalar(statement=statement)
        if user_model is None:
            return "failure", UserWithIdDoesNotExistError(id=id_)
        return "success", user_model

    async def _read_user_by_email(
        self, email: str
    ) -> Result[UserWithEmailDoesNotExistError, UserModel]:
        statement = (
            select(UserModel)
            .where(UserModel.email == email)
            .options(self._LOADER_OPTION)
        )
        user_model = await self._session.scalar(statement=statement)
        if user_model is None:
            return "failure", UserWithEmailDoesNotExistError(email=email)
        return "success", user_model

    async def _read_user_by_id(
        self, id_: UUID
    ) -> Result[UserWithIdDoesNotExistError, UserModel]:
        user_model = await self._session.get(
            UserModel,
            id_,
            options=(self._LOADER_OPTION,),
        )
        if user_model is None:
            return "failure", UserWithIdDoesNotExistError(id=id_)
        return "success", user_model

    async def _read_users(self) -> tuple[UserModel, ...]:
        statement = select(UserModel).options(self._LOADER_OPTION)
        scalars = await self._session.scalars(statement=statement)
        return tuple(scalars.all())

    async def _update_user(self, user: User) -> Result[_UpdateUserError, UserModel]:
        statement = (
            update(UserModel)
            .where(UserModel.id == user.id)
            .values(email=user.email)
            .returning(UserModel)
            .options(self._LOADER_OPTION)
        )
        try:
            user_model = await self._session.scalar(statement=statement)
        except IntegrityError as e:
            match str(e.orig):
                case "UNIQUE constraint failed: user.email":
                    return "failure", UserWithEmailAlreadyExistsError(email=user.email)
                case _:  # pragma: no cover
                    raise
        else:
            if user_model is None:
                return "failure", UserWithIdDoesNotExistError(id=user.id)
            return "success", user_model

    def create_user(
        self, user: User
    ) -> AwaitableResult[_CreateUserError, UserWithSubscriptionsWithProducts]:
        return (
            Wrapper(user)
            .map_to_awaitable_result(self._create_user)
            .map_success(UserModel.to_user_with_subscriptions_with_products)
            .core
        )

    def delete_user(
        self, id_: UUID
    ) -> AwaitableResult[
        UserWithIdDoesNotExistError, UserWithSubscriptionsWithProducts
    ]:
        return (
            Wrapper(id_)
            .map_to_awaitable_result(self._delete_user)
            .map_success(UserModel.to_user_with_subscriptions_with_products)
            .core
        )

    def read_user_by_email(
        self, email: str
    ) -> AwaitableResult[
        UserWithEmailDoesNotExistError, UserWithSubscriptionsWithProducts
    ]:
        return (
            Wrapper(email)
            .map_to_awaitable_result(self._read_user_by_email)
            .map_success(UserModel.to_user_with_subscriptions_with_products)
            .core
        )

    def read_user_by_id(
        self, id_: UUID
    ) -> AwaitableResult[
        UserWithIdDoesNotExistError, UserWithSubscriptionsWithProducts
    ]:
        return (
            Wrapper(id_)
            .map_to_awaitable_result(self._read_user_by_id)
            .map_success(UserModel.to_user_with_subscriptions_with_products)
            .core
        )

    def read_users(self) -> AwaitableTuple[UserWithSubscriptionsWithProducts]:
        return (
            AwaitableTupleWrapper(self._read_users())
            .map(UserModel.to_user_with_subscriptions_with_products)
            .core
        )

    def update_user(
        self, user: User
    ) -> AwaitableResult[_UpdateUserError, UserWithSubscriptionsWithProducts]:
        return (
            Wrapper(user)
            .map_to_awaitable_result(self._update_user)
            .map_success(UserModel.to_user_with_subscriptions_with_products)
            .core
        )
