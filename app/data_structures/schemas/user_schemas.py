from uuid import UUID

from pydantic import BaseModel

from app.data_structures.domain.user import User, UserWithSubscriptionsWithProducts
from app.data_structures.schemas.subscription_schemas import SubscriptionResponse


class _UserSchemaWithoutId(BaseModel, frozen=True):
    email: str


class _UserSchemaWithId(_UserSchemaWithoutId, frozen=True):
    id: UUID


class PostUserRequest(_UserSchemaWithId, frozen=True):
    def to_user(self) -> User:
        return User(id=self.id, email=self.email)


class PutUserRequest(_UserSchemaWithoutId, frozen=True):
    def to_user(self, id_: UUID) -> User:
        return User(id=id_, email=self.email)


class UserResponse(_UserSchemaWithId, frozen=True):
    subscriptions: tuple[SubscriptionResponse, ...]

    @staticmethod
    def from_user_with_subscriptions_with_products(
        user: UserWithSubscriptionsWithProducts,
    ) -> UserResponse:
        subscriptions = tuple(
            SubscriptionResponse.from_subscription_with_product(subscription)
            for subscription in user.subscriptions_with_products
        )
        return UserResponse(id=user.id, email=user.email, subscriptions=subscriptions)
