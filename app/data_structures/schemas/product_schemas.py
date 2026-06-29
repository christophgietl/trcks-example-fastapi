from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field

from app.data_structures.domain.product import Product, ProductStatus


class _ProductSchemaWithoutId(BaseModel, frozen=True):
    monthly_fee_in_euros: Annotated[Decimal, Field(decimal_places=2, ge=0)]
    name: str
    status: ProductStatus


class _ProductSchemaWithId(_ProductSchemaWithoutId, frozen=True):
    id: UUID


class PostProductRequest(_ProductSchemaWithId, frozen=True):
    def to_product(self) -> Product:
        return Product(
            id=self.id,
            monthly_fee_in_euros=self.monthly_fee_in_euros,
            name=self.name,
            status=self.status,
        )


class PutProductRequest(_ProductSchemaWithoutId, frozen=True):
    def to_product(self, id_: UUID) -> Product:
        return Product(
            id=id_,
            monthly_fee_in_euros=self.monthly_fee_in_euros,
            name=self.name,
            status=self.status,
        )


class ProductResponse(_ProductSchemaWithId, frozen=True):
    @staticmethod
    def from_product(product: Product) -> ProductResponse:
        return ProductResponse(
            id=product.id,
            monthly_fee_in_euros=product.monthly_fee_in_euros,
            name=product.name,
            status=product.status,
        )
