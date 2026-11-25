from typing import TypedDict, final
from uuid import UUID

from subscription_management.data_structures.domain.subscription import (
    SubscriptionWithProduct,
    SubscriptionWithUserIdAndProductId,
)
from subscription_management.data_structures.schemas.product_schemas import (
    ProductResponse,
    map_product_to_product_response,
)


class _SubscriptionSchemaWithoutId(TypedDict):
    is_active: bool


class _SubscriptionSchemaWithId(_SubscriptionSchemaWithoutId):
    id: UUID


@final
class PostSubscriptionRequest(_SubscriptionSchemaWithId):
    user_id: UUID
    product_id: UUID


@final
class PutSubscriptionRequest(_SubscriptionSchemaWithoutId):
    user_id: UUID
    product_id: UUID


@final
class SubscriptionResponse(_SubscriptionSchemaWithId):
    product: ProductResponse


def map_post_subscription_request_to_subscription_with_user_id_and_product_id(
    request: PostSubscriptionRequest,
) -> SubscriptionWithUserIdAndProductId:
    return SubscriptionWithUserIdAndProductId(**request)


def map_put_subscription_request_to_subscription_with_user_id_and_product_id(
    id_: UUID, request: PutSubscriptionRequest
) -> SubscriptionWithUserIdAndProductId:
    return SubscriptionWithUserIdAndProductId(id=id_, **request)


def map_subscription_with_product_to_subscription_response(
    subscription: SubscriptionWithProduct,
) -> SubscriptionResponse:
    return SubscriptionResponse(
        id=subscription.id,
        is_active=subscription.is_active,
        product=map_product_to_product_response(subscription.product),
    )
