from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, final

from fastapi import Depends
from trcks.oop import Wrapper

from subscription_management.data_structures.domain.do_not_update import (
    DO_NOT_UPDATE,
)
from subscription_management.data_structures.domain.user import User
from subscription_management.logic.repositories.user_repository import (
    UserRepositoryDep,  # noqa: TC001
)

if TYPE_CHECKING:
    from uuid import UUID

    from trcks import AwaitableResult, AwaitableTuple

    from subscription_management.data_structures.domain.user import (
        UserUpdate,
        UserWithSubscriptionsWithProducts,
    )
    from subscription_management.data_structures.domain.user_error import (
        UserWithEmailAlreadyExistsError,
        UserWithEmailDoesNotExistError,
        UserWithIdAlreadyExistsError,
        UserWithIdDoesNotExistError,
    )


type UserServiceDep = Annotated[UserService, Depends()]


@final
@dataclass(frozen=True, kw_only=True, slots=True)
class UserService:
    _user_repository: UserRepositoryDep

    def _add_old_user(
        self, user_update: UserUpdate
    ) -> AwaitableResult[UserWithIdDoesNotExistError, User]:
        return (
            Wrapper(user_update.id)
            .map_to_awaitable_result(self._user_repository.read_user_by_id)
            .map_success(self._merge_user_update, user_update=user_update)
            .core
        )

    @staticmethod
    def _merge_user_update(
        before: UserWithSubscriptionsWithProducts, user_update: UserUpdate
    ) -> User:
        return User(
            id=before.id,
            email=(
                before.email
                if user_update.email is DO_NOT_UPDATE
                else user_update.email
            ),
        )

    def create_user(
        self, user: User
    ) -> AwaitableResult[
        UserWithEmailAlreadyExistsError | UserWithIdAlreadyExistsError,
        UserWithSubscriptionsWithProducts,
    ]:
        return self._user_repository.create_user(user)

    def delete_user(
        self, id_: UUID
    ) -> AwaitableResult[
        UserWithIdDoesNotExistError, UserWithSubscriptionsWithProducts
    ]:
        return self._user_repository.delete_user(id_)

    def read_user_by_email(
        self, email: str
    ) -> AwaitableResult[
        UserWithEmailDoesNotExistError, UserWithSubscriptionsWithProducts
    ]:
        return self._user_repository.read_user_by_email(email)

    def read_user_by_id(
        self, id_: UUID
    ) -> AwaitableResult[
        UserWithIdDoesNotExistError, UserWithSubscriptionsWithProducts
    ]:
        return self._user_repository.read_user_by_id(id_)

    def read_users(self) -> AwaitableTuple[UserWithSubscriptionsWithProducts]:
        return self._user_repository.read_users()

    def update_user(
        self, user_update: UserUpdate
    ) -> AwaitableResult[
        UserWithEmailAlreadyExistsError | UserWithIdDoesNotExistError,
        UserWithSubscriptionsWithProducts,
    ]:
        return (
            Wrapper(user_update)
            .map_to_awaitable_result(self._add_old_user)
            .map_success_to_awaitable_result(self._user_repository.update_user)
            .core
        )
