from typing import TYPE_CHECKING
from uuid import uuid7

import pytest

from subscription_management.data_structures.domain.user import User
from subscription_management.data_structures.domain.user_error import (
    UserWithIdDoesNotExistError,
)
from subscription_management.logic.repositories.user_repository import UserRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class TestUserRepository:
    @pytest.fixture
    def repository(self, session: AsyncSession) -> UserRepository:
        return UserRepository(_session=session)

    async def test_update_user_returns_failure_for_nonexistent_id(
        self, repository: UserRepository
    ) -> None:
        nonexistent_user = User(id=uuid7(), email="unknown@example.com")
        result = await repository.update_user(nonexistent_user)

        assert result == (
            "failure",
            UserWithIdDoesNotExistError(id=nonexistent_user.id),
        )
