from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, ClassVar, Final, Literal, TypeAlias

from fastapi import Depends
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.interfaces import LoaderOption  # noqa: TC002

from app.data_structures.domain.user import User, UserWithSubscriptionsWithProducts
from app.data_structures.models import SubscriptionModel, UserModel
from app.database import AsyncSessionDep  # noqa: TC001

if TYPE_CHECKING:
    from uuid import UUID

    from trcks import Failure, Result

type _BaseUserResult = Result[
    Literal["User does not exist"], UserWithSubscriptionsWithProducts
]


@dataclass(frozen=True, kw_only=True, slots=True)
class UserRepository:
    _LOADER_OPTION: ClassVar[Final[LoaderOption]] = selectinload(
        UserModel.subscriptions
    ).selectinload(SubscriptionModel.product)

    _session: AsyncSessionDep

    @staticmethod
    def _to_base_user_result(user_model: UserModel | None) -> _BaseUserResult:
        if user_model is None:
            return "failure", "User does not exist"
        return "success", user_model.to_user_with_subscriptions_with_products()

    async def create_user(
        self, user: User
    ) -> Result[Literal["Email already exists", "ID already exists"], None]:
        user_model = UserModel.from_user(user)
        self._session.add(user_model)
        try:
            await self._session.flush()
        except IntegrityError as e:
            match str(e.orig):
                case "UNIQUE constraint failed: user.id":
                    return "failure", "ID already exists"
                case "UNIQUE constraint failed: user.email":
                    return "failure", "Email already exists"
                case _:  # pragma: no cover
                    raise
        else:
            return "success", None

    async def delete_user(self, id_: UUID) -> _BaseUserResult:
        deleted_user_model = await self._session.scalar(
            delete(UserModel)
            .where(UserModel.id == id_)
            .returning(UserModel)
            .options(self._LOADER_OPTION)
        )
        return self._to_base_user_result(deleted_user_model)

    async def read_user_by_email(self, email: str) -> _BaseUserResult:
        user_model = await self._session.scalar(
            select(UserModel)
            .where(UserModel.email == email)
            .options(self._LOADER_OPTION)
        )
        return self._to_base_user_result(user_model)

    async def read_user_by_id(self, id_: UUID) -> _BaseUserResult:
        user_model = await self._session.get(
            UserModel,
            id_,
            options=(self._LOADER_OPTION,),
        )
        return self._to_base_user_result(user_model)

    async def read_users(self) -> tuple[UserWithSubscriptionsWithProducts, ...]:
        scalars = await self._session.scalars(
            select(UserModel).options(self._LOADER_OPTION)
        )
        user_models = scalars.all()
        return tuple(
            user_model.to_user_with_subscriptions_with_products()
            for user_model in user_models
        )

    async def update_user(
        self, user: User
    ) -> _BaseUserResult | Failure[Literal["Email already exists"]]:
        try:
            updated_user_model = await self._session.scalar(
                update(UserModel)
                .where(UserModel.id == user.id)
                .values(email=user.email)
                .returning(UserModel)
                .options(self._LOADER_OPTION)
            )
        except IntegrityError as e:
            match str(e.orig):
                case "UNIQUE constraint failed: user.email":
                    return "failure", "Email already exists"
                case _:  # pragma: no cover
                    raise
        else:
            return self._to_base_user_result(updated_user_model)


# FastAPI does not support the type keyword when used for dependencies
# as of October 2025 (see https://github.com/fastapi/fastapi/issues/10719):
UserRepositoryDep: TypeAlias = Annotated[UserRepository, Depends()]  # noqa: UP040
