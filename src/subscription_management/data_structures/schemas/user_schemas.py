# pyright: reportUninitializedInstanceVariable=false
# See https://github.com/pydantic/pydantic/issues/10377#issuecomment-2342806423
from typing import Self, final
from uuid import UUID

from pydantic import MISSING, BaseModel
from trcks.oop import TupleWrapper

from subscription_management.data_structures.domain.do_not_update import (
    DO_NOT_UPDATE,
)
from subscription_management.data_structures.domain.user import (
    User,
    UserUpdate,
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
class PutUserRequest(BaseModel, frozen=True):
    email: str | MISSING = MISSING

    def to_user_update(self, id_: UUID) -> UserUpdate:
        return UserUpdate(
            id=id_,
            email=self.email if self.email is not MISSING else DO_NOT_UPDATE,
        )


@final
class UserResponse(_UserSchemaWithId, frozen=True):
    subscriptions: tuple[SubscriptionResponse, ...]

    @classmethod
    def from_user_with_subscriptions_with_products(
        cls, user: UserWithSubscriptionsWithProducts
    ) -> Self:
        subscriptions = (
            TupleWrapper(user.subscriptions_with_products)
            .map(SubscriptionResponse.from_subscription_with_product)
            .core
        )
        return cls(id=user.id, email=user.email, subscriptions=subscriptions)
