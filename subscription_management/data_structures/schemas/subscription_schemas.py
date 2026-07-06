# pyright: reportUninitializedInstanceVariable=false
# See https://github.com/pydantic/pydantic/issues/10377#issuecomment-2342806423
from typing import TYPE_CHECKING, final
from uuid import UUID

from pydantic import BaseModel

from subscription_management.data_structures.domain.subscription import (
    SubscriptionWithUserIdAndProductId,
)
from subscription_management.data_structures.schemas.product_schemas import (
    ProductResponse,
)

if TYPE_CHECKING:
    from subscription_management.data_structures.domain.subscription import (
        SubscriptionWithProduct,
    )


class _SubscriptionSchemaWithoutId(BaseModel, frozen=True):
    is_active: bool


class _SubscriptionSchemaWithId(_SubscriptionSchemaWithoutId, frozen=True):
    id: UUID


@final
class PostSubscriptionRequest(_SubscriptionSchemaWithId, frozen=True):
    user_id: UUID
    product_id: UUID

    def to_subscription_with_user_id_and_product_id(
        self,
    ) -> SubscriptionWithUserIdAndProductId:
        return SubscriptionWithUserIdAndProductId(
            id=self.id,
            is_active=self.is_active,
            user_id=self.user_id,
            product_id=self.product_id,
        )


@final
class PutSubscriptionRequest(_SubscriptionSchemaWithoutId, frozen=True):
    user_id: UUID
    product_id: UUID

    def to_subscription_with_user_id_and_product_id(
        self, id_: UUID
    ) -> SubscriptionWithUserIdAndProductId:
        return SubscriptionWithUserIdAndProductId(
            id=id_,
            is_active=self.is_active,
            user_id=self.user_id,
            product_id=self.product_id,
        )


@final
class SubscriptionResponse(_SubscriptionSchemaWithId, frozen=True):
    product: ProductResponse

    @staticmethod
    def from_subscription_with_product(
        subscription: SubscriptionWithProduct,
    ) -> SubscriptionResponse:
        return SubscriptionResponse(
            id=subscription.id,
            is_active=subscription.is_active,
            product=ProductResponse.from_product(subscription.product),
        )
