from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, Literal, final

from fastapi import Depends

from app.logic.repositories.user_repository import UserRepositoryDep  # noqa: TC001

if TYPE_CHECKING:
    from uuid import UUID

    from trcks import AwaitableResult, AwaitableTuple

    from app.data_structures.domain.user import User, UserWithSubscriptionsWithProducts

type _AwaitableDeleteOrReadUserResult = AwaitableResult[
    Literal["User does not exist"], UserWithSubscriptionsWithProducts
]

type UserServiceDep = Annotated[UserService, Depends()]


@final
@dataclass(frozen=True, kw_only=True, slots=True)
class UserService:
    _user_repository: UserRepositoryDep

    def create_user(
        self, user: User
    ) -> AwaitableResult[
        Literal["Email already exists", "ID already exists"],
        UserWithSubscriptionsWithProducts,
    ]:
        return self._user_repository.create_user(user)

    def delete_user(self, id_: UUID) -> _AwaitableDeleteOrReadUserResult:
        return self._user_repository.delete_user(id_)

    def read_user_by_email(self, email: str) -> _AwaitableDeleteOrReadUserResult:
        return self._user_repository.read_user_by_email(email)

    def read_user_by_id(self, id_: UUID) -> _AwaitableDeleteOrReadUserResult:
        return self._user_repository.read_user_by_id(id_)

    def read_users(self) -> AwaitableTuple[UserWithSubscriptionsWithProducts]:
        return self._user_repository.read_users()

    def update_user(
        self, user: User
    ) -> AwaitableResult[
        Literal["User does not exist", "Email already exists"],
        UserWithSubscriptionsWithProducts,
    ]:
        return self._user_repository.update_user(user)
