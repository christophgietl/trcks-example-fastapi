from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import uuid7

import pytest

from subscription_management.data_structures.domain.product import Product
from subscription_management.data_structures.domain.product_error import (
    ProductWithIdDoesNotExistError,
)
from subscription_management.logic.repositories.product_repository import (
    ProductRepository,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class TestProductRepository:
    @pytest.fixture
    def repository(self, session: AsyncSession) -> ProductRepository:
        return ProductRepository(_session=session)

    async def test_delete_product_returns_failure_for_nonexistent_id(
        self, repository: ProductRepository
    ) -> None:
        nonexistent_product_id = uuid7()
        result = await repository.delete_product(nonexistent_product_id)

        assert result == (
            "failure",
            ProductWithIdDoesNotExistError(id=nonexistent_product_id),
        )

    async def test_update_product_returns_failure_for_nonexistent_id(
        self, repository: ProductRepository
    ) -> None:
        nonexistent_product = Product(
            id=uuid7(),
            monthly_fee_in_euros=Decimal("4.99"),
            name="Unknown Product",
            status="draft",
        )
        result = await repository.update_product(nonexistent_product)

        assert result == (
            "failure",
            ProductWithIdDoesNotExistError(id=nonexistent_product.id),
        )
