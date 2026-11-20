from typing import TYPE_CHECKING, TypedDict, final
from uuid import UUID

from trcks.oop import TupleWrapper

from subscription_management.data_structures.domain.user import User
from subscription_management.data_structures.schemas.subscription_schemas import (
    SubscriptionResponse,
    from_subscription_with_product,
)

if TYPE_CHECKING:
    from subscription_management.data_structures.domain.user import (
        UserWithSubscriptionsWithProducts,
    )


class _UserSchemaWithoutId(TypedDict):
    email: str


class _UserSchemaWithId(_UserSchemaWithoutId):
    id: UUID


@final
class PostUserRequest(_UserSchemaWithId):
    pass


@final
class PutUserRequest(_UserSchemaWithoutId):
    pass


@final
class UserResponse(_UserSchemaWithId):
    subscriptions: tuple[SubscriptionResponse, ...]


def from_user_with_subscriptions_with_products(
    user: UserWithSubscriptionsWithProducts,
) -> UserResponse:
    subscriptions = (
        TupleWrapper(user.subscriptions_with_products)
        .map(from_subscription_with_product)
        .core
    )
    return {"id": user.id, "email": user.email, "subscriptions": subscriptions}


def to_user_from_post_request(post_user_request: PostUserRequest) -> User:
    return User(id=post_user_request["id"], email=post_user_request["email"])


def to_user_from_put_request(put_user_request: PutUserRequest, id_: UUID) -> User:
    return User(id=id_, email=put_user_request["email"])
