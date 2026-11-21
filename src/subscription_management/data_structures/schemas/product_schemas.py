from decimal import Decimal
from typing import Annotated, TypedDict, final
from uuid import UUID

from pydantic import Field

from subscription_management.data_structures.domain.product import (
    Product,
    ProductStatus,
)


class _ProductSchemaWithoutId(TypedDict):
    monthly_fee_in_euros: Annotated[
        Decimal, Field(decimal_places=2, ge=Decimal("0.00"))
    ]
    name: str
    status: ProductStatus


class _ProductSchemaWithId(_ProductSchemaWithoutId):
    id: UUID


@final
class PostProductRequest(_ProductSchemaWithId):
    pass


@final
class PutProductRequest(_ProductSchemaWithoutId):
    pass


@final
class ProductResponse(_ProductSchemaWithId):
    pass


def map_post_product_request_to_product(request: PostProductRequest) -> Product:
    return Product(**request)


def map_product_to_product_response(product: Product) -> ProductResponse:
    return ProductResponse(
        id=product.id,
        monthly_fee_in_euros=product.monthly_fee_in_euros,
        name=product.name,
        status=product.status,
    )


def map_put_product_request_to_product(
    id_: UUID, request: PutProductRequest
) -> Product:
    return Product(id=id_, **request)
