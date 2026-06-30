from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import uuid7

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.data_structures.models import (
    ProductModel,
    SubscriptionModel,
    UserModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def test_foreign_keys_are_enforced(session: AsyncSession) -> None:
    product_id = uuid7()
    nonexistent_user_id = uuid7()
    async with session.begin():
        session.add(
            ProductModel(
                id=product_id,
                monthly_fee_in_euros=Decimal("9.99"),
                name="Product 1",
                status="published",
            )
        )
        await session.flush()

    subscription = SubscriptionModel(
        id=uuid7(),
        is_active=True,
        product_id=product_id,
        user_id=nonexistent_user_id,
    )
    with pytest.raises(IntegrityError):
        async with session.begin():
            session.add(subscription)


async def test_on_delete_cascade_removes_subscriptions(session: AsyncSession) -> None:
    product_id = uuid7()
    user_id = uuid7()
    subscription_id = uuid7()
    async with session.begin():
        session.add_all(
            [
                ProductModel(
                    id=product_id,
                    monthly_fee_in_euros=Decimal("9.99"),
                    name="Product 1",
                    status="published",
                ),
                UserModel(id=user_id, email="user@example.com"),
                SubscriptionModel(
                    id=subscription_id,
                    is_active=True,
                    product_id=product_id,
                    user_id=user_id,
                ),
            ]
        )
        await session.flush()

    async with session.begin():
        user = await session.get(UserModel, user_id)
        assert user is not None
        await session.delete(user)

    remaining_user_ids = await session.scalars(select(SubscriptionModel.user_id))

    assert remaining_user_ids.all() == []
