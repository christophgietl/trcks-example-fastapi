# pyright: reportUninitializedInstanceVariable=false
# See https://github.com/pydantic/pydantic/issues/10377#issuecomment-2342806423
from decimal import Decimal
from typing import Annotated, Self, final
from uuid import UUID

from pydantic import MISSING, BaseModel, Field

from subscription_management.data_structures.domain.do_not_update import (
    DO_NOT_UPDATE,
)
from subscription_management.data_structures.domain.product import (
    Product,
    ProductStatus,
    ProductUpdate,
)


class _ProductSchemaWithoutId(BaseModel, frozen=True):
    monthly_fee_in_euros: Annotated[
        Decimal, Field(decimal_places=2, ge=Decimal("0.00"))
    ]
    name: str
    status: ProductStatus


class _ProductSchemaWithId(_ProductSchemaWithoutId, frozen=True):
    id: UUID


@final
class PostProductRequest(_ProductSchemaWithId, frozen=True):
    def to_product(self) -> Product:
        return Product(
            id=self.id,
            monthly_fee_in_euros=self.monthly_fee_in_euros,
            name=self.name,
            status=self.status,
        )


@final
class PutProductRequest(BaseModel, frozen=True):
    monthly_fee_in_euros: Annotated[
        Decimal | MISSING, Field(decimal_places=2, ge=Decimal("0.00"))
    ] = MISSING
    name: str | MISSING = MISSING
    status: ProductStatus | MISSING = MISSING

    def to_product_update(self, id_: UUID) -> ProductUpdate:
        return ProductUpdate(
            id=id_,
            monthly_fee_in_euros=(
                self.monthly_fee_in_euros
                if self.monthly_fee_in_euros is not MISSING
                else DO_NOT_UPDATE
            ),
            name=self.name if self.name is not MISSING else DO_NOT_UPDATE,
            status=self.status if self.status is not MISSING else DO_NOT_UPDATE,
        )


@final
class ProductResponse(_ProductSchemaWithId, frozen=True):
    @classmethod
    def from_product(cls, product: Product) -> Self:
        return cls(
            id=product.id,
            monthly_fee_in_euros=product.monthly_fee_in_euros,
            name=product.name,
            status=product.status,
        )
