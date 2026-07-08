from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import uuid7

from subscription_management.data_structures.domain.product import Product
from subscription_management.data_structures.domain.product_error import (
    ProductWithIdDoesNotExistError,
)
from subscription_management.logic.repositories.product_repository import (
    ProductRepository,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def test_delete_product_returns_failure_for_nonexistent_id(
    session: AsyncSession,
) -> None:
    repository = ProductRepository(_session=session)
    id_ = uuid7()

    result = await repository.delete_product(id_)

    assert result == ("failure", ProductWithIdDoesNotExistError(id=id_))


async def test_update_product_returns_failure_for_nonexistent_id(
    session: AsyncSession,
) -> None:
    repository = ProductRepository(_session=session)
    product = Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("4.99"),
        name="Unknown Product",
        status="draft",
    )

    result = await repository.update_product(product)

    assert result == ("failure", ProductWithIdDoesNotExistError(id=product.id))
