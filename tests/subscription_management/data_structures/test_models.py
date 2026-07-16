from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import uuid7

import pytest
from sqlalchemy.exc import IntegrityError

from subscription_management.data_structures.domain.product import Product
from subscription_management.data_structures.domain.subscription import (
    SubscriptionWithUserIdAndProductId,
)
from subscription_management.data_structures.domain.user import User
from subscription_management.data_structures.models import SubscriptionModel, UserModel
from subscription_management.testing.helpers import (
    insert_products,
    insert_subscriptions,
    insert_users,
    select_subscriptions,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class TestSubscriptionModel:
    async def test_foreign_key_relationships_are_validated_on_insert(
        self, session: AsyncSession
    ) -> None:
        product = Product(
            id=uuid7(),
            monthly_fee_in_euros=Decimal("9.99"),
            name="Product 1",
            status="published",
        )
        await insert_products(session, product)

        nonexistent_user_id = uuid7()
        subscription_model = SubscriptionModel(
            id=uuid7(),
            is_active=True,
            product_id=product.id,
            user_id=nonexistent_user_id,
        )
        with pytest.raises(IntegrityError):
            async with session.begin():
                session.add(subscription_model)

    async def test_subscriptions_are_deleted_on_user_deletion(
        self, session: AsyncSession
    ) -> None:
        product = Product(
            id=uuid7(),
            monthly_fee_in_euros=Decimal("9.99"),
            name="Product 1",
            status="published",
        )
        await insert_products(session, product)
        user = User(id=uuid7(), email="user@example.com")
        await insert_users(session, user)
        subscription = SubscriptionWithUserIdAndProductId(
            id=uuid7(),
            is_active=True,
            product_id=product.id,
            user_id=user.id,
        )
        await insert_subscriptions(session, subscription)

        async with session.begin():
            user_model = await session.get(UserModel, user.id)
            assert user_model is not None
            await session.delete(user_model)

        subscriptions = await select_subscriptions(session)
        assert subscriptions == ()
