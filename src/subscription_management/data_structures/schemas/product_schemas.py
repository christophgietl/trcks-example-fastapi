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


def from_product(product: Product) -> ProductResponse:
    return {
        "id": product.id,
        "monthly_fee_in_euros": product.monthly_fee_in_euros,
        "name": product.name,
        "status": product.status,
    }


def to_product_from_post_request(
    post_product_request: PostProductRequest,
) -> Product:
    return Product(
        id=post_product_request["id"],
        monthly_fee_in_euros=post_product_request["monthly_fee_in_euros"],
        name=post_product_request["name"],
        status=post_product_request["status"],
    )


def to_product_from_put_request(
    put_product_request: PutProductRequest, id_: UUID
) -> Product:
    return Product(
        id=id_,
        monthly_fee_in_euros=put_product_request["monthly_fee_in_euros"],
        name=put_product_request["name"],
        status=put_product_request["status"],
    )
