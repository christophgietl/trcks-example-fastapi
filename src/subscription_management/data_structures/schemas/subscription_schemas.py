# pyright: reportUninitializedInstanceVariable=false
# See https://github.com/pydantic/pydantic/issues/10377#issuecomment-2342806423
from typing import TYPE_CHECKING, Self, final
from uuid import UUID

from pydantic import MISSING, BaseModel

from subscription_management.data_structures.domain.do_not_update import (
    DO_NOT_UPDATE,
)
from subscription_management.data_structures.domain.subscription import (
    SubscriptionUpdate,
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
class PutSubscriptionRequest(BaseModel, frozen=True):
    is_active: bool | MISSING = MISSING
    user_id: UUID | MISSING = MISSING
    product_id: UUID | MISSING = MISSING

    def to_subscription_update(self, id_: UUID) -> SubscriptionUpdate:
        return SubscriptionUpdate(
            id=id_,
            is_active=(DO_NOT_UPDATE if self.is_active is MISSING else self.is_active),
            user_id=(DO_NOT_UPDATE if self.user_id is MISSING else self.user_id),
            product_id=(
                DO_NOT_UPDATE if self.product_id is MISSING else self.product_id
            ),
        )


@final
class SubscriptionResponse(_SubscriptionSchemaWithId, frozen=True):
    product: ProductResponse

    @classmethod
    def from_subscription_with_product(
        cls, subscription: SubscriptionWithProduct
    ) -> Self:
        return cls(
            id=subscription.id,
            is_active=subscription.is_active,
            product=ProductResponse.from_product(subscription.product),
        )
