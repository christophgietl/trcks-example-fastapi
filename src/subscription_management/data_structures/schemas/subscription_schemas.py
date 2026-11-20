from typing import TYPE_CHECKING, TypedDict, final
from uuid import UUID

from subscription_management.data_structures.domain.subscription import (
    SubscriptionWithUserIdAndProductId,
)
from subscription_management.data_structures.schemas.product_schemas import (
    ProductResponse,
    from_product,
)

if TYPE_CHECKING:
    from subscription_management.data_structures.domain.subscription import (
        SubscriptionWithProduct,
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


def from_subscription_with_product(
    subscription: SubscriptionWithProduct,
) -> SubscriptionResponse:
    return {
        "id": subscription.id,
        "is_active": subscription.is_active,
        "product": from_product(subscription.product),
    }


def to_subscription_with_user_id_and_product_id_from_post_request(
    post_subscription_request: PostSubscriptionRequest,
) -> SubscriptionWithUserIdAndProductId:
    return SubscriptionWithUserIdAndProductId(
        id=post_subscription_request["id"],
        is_active=post_subscription_request["is_active"],
        user_id=post_subscription_request["user_id"],
        product_id=post_subscription_request["product_id"],
    )


def to_subscription_with_user_id_and_product_id_from_put_request(
    put_subscription_request: PutSubscriptionRequest, id_: UUID
) -> SubscriptionWithUserIdAndProductId:
    return SubscriptionWithUserIdAndProductId(
        id=id_,
        is_active=put_subscription_request["is_active"],
        user_id=put_subscription_request["user_id"],
        product_id=put_subscription_request["product_id"],
    )
