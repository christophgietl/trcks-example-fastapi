from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import uuid7

import pytest

from subscription_management.data_structures.domain.product import Product
from subscription_management.data_structures.domain.subscription import (
    SubscriptionWithUserIdAndProductId,
)
from subscription_management.data_structures.domain.subscription_error import (
    SubscriptionWithIdDoesNotExistError,
)
from subscription_management.data_structures.domain.user import User
from subscription_management.logic.repositories.product_repository import (
    ProductRepository,
)
from subscription_management.logic.repositories.subscription_repository import (
    SubscriptionRepository,
)
from subscription_management.logic.repositories.user_repository import UserRepository
from subscription_management.testing.helpers import insert_products, insert_users

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class TestSubscriptionRepository:
    @pytest.fixture
    def repository(self, session: AsyncSession) -> SubscriptionRepository:
        return SubscriptionRepository(
            _session=session,
            _product_repository=ProductRepository(_session=session),
            _user_repository=UserRepository(_session=session),
        )

    async def test_update_subscription_returns_failure_for_nonexistent_id(
        self, repository: SubscriptionRepository, session: AsyncSession
    ) -> None:
        product = Product(
            id=uuid7(),
            monthly_fee_in_euros=Decimal("9.99"),
            name="Test Product",
            status="published",
        )
        user = User(id=uuid7(), email="spam@foo.org")
        await insert_products(session, product)
        await insert_users(session, user)

        nonexistent_subscription = SubscriptionWithUserIdAndProductId(
            id=uuid7(),
            is_active=True,
            user_id=user.id,
            product_id=product.id,
        )
        result = await repository.update_subscription(nonexistent_subscription)

        assert result == (
            "failure",
            SubscriptionWithIdDoesNotExistError(id=nonexistent_subscription.id),
        )
