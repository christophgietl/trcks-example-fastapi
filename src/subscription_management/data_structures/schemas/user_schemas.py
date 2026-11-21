from typing import TypedDict, final
from uuid import UUID

from trcks.oop import TupleWrapper

from subscription_management.data_structures.domain.user import (
    User,
    UserWithSubscriptionsWithProducts,
)
from subscription_management.data_structures.schemas.subscription_schemas import (
    SubscriptionResponse,
    map_subscription_with_product_to_subscription_response,
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


def map_post_user_request_to_user(request: PostUserRequest) -> User:
    return User(**request)


def map_put_user_request_to_user(id_: UUID, request: PutUserRequest) -> User:
    return User(id=id_, **request)


def map_user_with_subscriptions_with_products_to_user_response(
    user: UserWithSubscriptionsWithProducts,
) -> UserResponse:
    subscriptions = (
        TupleWrapper(user.subscriptions_with_products)
        .map(map_subscription_with_product_to_subscription_response)
        .core
    )
    return UserResponse(
        id=user.id,
        email=user.email,
        subscriptions=subscriptions,
    )
