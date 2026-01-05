from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, Literal, TypeAlias

from fastapi import Depends

from app.logic.repositories.user_repository import UserRepositoryDep  # noqa: TC001

if TYPE_CHECKING:
    from collections.abc import Awaitable
    from uuid import UUID

    from trcks import AwaitableResult

    from app.data_structures.domain.user import User, UserWithSubscriptionsWithProducts


@dataclass(frozen=True, kw_only=True, slots=True)
class UserService:
    _user_repository: UserRepositoryDep

    def create_user(
        self, user: User
    ) -> AwaitableResult[Literal["Email already exists", "ID already exists"], None]:
        return self._user_repository.create_user(user)

    def delete_user(
        self, id_: UUID
    ) -> AwaitableResult[
        Literal["User does not exist"], UserWithSubscriptionsWithProducts
    ]:
        return self._user_repository.delete_user(id_)

    def read_user_by_email(
        self, email: str
    ) -> AwaitableResult[
        Literal["User does not exist"], UserWithSubscriptionsWithProducts
    ]:
        return self._user_repository.read_user_by_email(email)

    def read_user_by_id(
        self, id_: UUID
    ) -> AwaitableResult[
        Literal["User does not exist"], UserWithSubscriptionsWithProducts
    ]:
        return self._user_repository.read_user_by_id(id_)

    def read_users(self) -> Awaitable[tuple[UserWithSubscriptionsWithProducts, ...]]:
        return self._user_repository.read_users()

    def update_user(
        self, user: User
    ) -> AwaitableResult[
        Literal["User does not exist", "Email already exists"],
        UserWithSubscriptionsWithProducts,
    ]:
        return self._user_repository.update_user(user)


# FastAPI does not support the type keyword when used for dependencies
# as of October 2025 (see https://github.com/fastapi/fastapi/issues/10719):
UserServiceDep: TypeAlias = Annotated[UserService, Depends()]  # noqa: UP040
