from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, ClassVar, Final, Literal, final

from fastapi import Depends
from sqlalchemy import delete, insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from trcks.oop import AwaitableTupleWrapper, Wrapper

from app.data_structures.domain.user import UserWithSubscriptionsWithProducts
from app.data_structures.models import SubscriptionModel, UserModel
from app.database import AsyncSessionDep  # noqa: TC001

if TYPE_CHECKING:
    from collections.abc import Awaitable
    from uuid import UUID

    from sqlalchemy.orm.interfaces import LoaderOption
    from trcks import AwaitableResult, AwaitableTuple, Result

    from app.data_structures.domain.user import User

type _AwaitableBaseUserResult = Awaitable[_BaseUserResult]
type _BaseUserResult = Result[
    Literal["User does not exist"], UserWithSubscriptionsWithProducts
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
        Literal["Email already exists", "ID already exists"],
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
                    return "failure", "ID already exists"
                case "UNIQUE constraint failed: user.email":
                    return "failure", "Email already exists"
                case _:  # pragma: no cover
                    raise
        else:
            return "success", scalars.one()

    async def _delete_user_model(self, id_: UUID) -> UserModel | None:
        statement = (
            delete(UserModel)
            .where(UserModel.id == id_)
            .returning(UserModel)
            .options(self._LOADER_OPTION)
        )
        return await self._session.scalar(statement=statement)

    async def _read_user_model_by_email(self, email: str) -> UserModel | None:
        statement = (
            select(UserModel)
            .where(UserModel.email == email)
            .options(self._LOADER_OPTION)
        )
        return await self._session.scalar(statement=statement)

    async def _read_user_model_by_id(self, id_: UUID) -> UserModel | None:
        return await self._session.get(
            UserModel,
            id_,
            options=(self._LOADER_OPTION,),
        )

    async def _read_user_models(self) -> tuple[UserModel, ...]:
        statement = select(UserModel).options(self._LOADER_OPTION)
        scalars = await self._session.scalars(statement=statement)
        return tuple(scalars.all())

    @staticmethod
    def _to_base_user_result(user_model: UserModel | None) -> _BaseUserResult:
        if user_model is None:
            return "failure", "User does not exist"
        return "success", user_model.to_user_with_subscriptions_with_products()

    async def _update_user_model(
        self, user: User
    ) -> Result[Literal["Email already exists"], UserModel | None]:
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
                    return "failure", "Email already exists"
                case _:  # pragma: no cover
                    raise
        else:
            return "success", updated_user_model

    def create_user(
        self, user: User
    ) -> AwaitableResult[
        Literal["Email already exists", "ID already exists"],
        UserWithSubscriptionsWithProducts,
    ]:
        return (
            Wrapper(user)
            .map_to_awaitable_result(self._create_user_model)
            .map_success(UserModel.to_user_with_subscriptions_with_products)
            .core
        )

    def delete_user(self, id_: UUID) -> _AwaitableBaseUserResult:
        return (
            Wrapper(id_)
            .map_to_awaitable(self._delete_user_model)
            .map(self._to_base_user_result)
            .core
        )

    def read_user_by_email(self, email: str) -> _AwaitableBaseUserResult:
        return (
            Wrapper(email)
            .map_to_awaitable(self._read_user_model_by_email)
            .map(self._to_base_user_result)
            .core
        )

    def read_user_by_id(self, id_: UUID) -> _AwaitableBaseUserResult:
        return (
            Wrapper(id_)
            .map_to_awaitable(self._read_user_model_by_id)
            .map(self._to_base_user_result)
            .core
        )

    def read_users(self) -> AwaitableTuple[UserWithSubscriptionsWithProducts]:
        return (
            AwaitableTupleWrapper(self._read_user_models())
            .map(UserModel.to_user_with_subscriptions_with_products)
            .core
        )

    def update_user(
        self, user: User
    ) -> AwaitableResult[
        Literal["Email already exists", "User does not exist"],
        UserWithSubscriptionsWithProducts,
    ]:
        return (
            Wrapper(user)
            .map_to_awaitable_result(self._update_user_model)
            .map_success_to_result(self._to_base_user_result)
            .core
        )
