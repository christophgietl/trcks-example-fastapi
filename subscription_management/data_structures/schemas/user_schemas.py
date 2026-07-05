# pyright: reportUninitializedInstanceVariable=false
# See https://github.com/pydantic/pydantic/issues/10377#issuecomment-2342806423
from typing import final
from uuid import UUID

from pydantic import BaseModel
from trcks.oop import TupleWrapper

from subscription_management.data_structures.domain.user import (
    User,
    UserWithSubscriptionsWithProducts,
)
from subscription_management.data_structures.schemas.subscription_schemas import (
    SubscriptionResponse,
)


class _UserSchemaWithoutId(BaseModel, frozen=True):
    email: str


class _UserSchemaWithId(_UserSchemaWithoutId, frozen=True):
    id: UUID


@final
class PostUserRequest(_UserSchemaWithId, frozen=True):
    def to_user(self) -> User:
        return User(id=self.id, email=self.email)


@final
class PutUserRequest(_UserSchemaWithoutId, frozen=True):
    def to_user(self, id_: UUID) -> User:
        return User(id=id_, email=self.email)


@final
class UserResponse(_UserSchemaWithId, frozen=True):
    subscriptions: tuple[SubscriptionResponse, ...]

    @staticmethod
    def from_user_with_subscriptions_with_products(
        user: UserWithSubscriptionsWithProducts,
    ) -> UserResponse:
        subscriptions = (
            TupleWrapper(user.subscriptions_with_products)
            .map(SubscriptionResponse.from_subscription_with_product)
            .core
        )
        return UserResponse(id=user.id, email=user.email, subscriptions=subscriptions)
