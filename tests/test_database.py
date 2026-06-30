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
    models = (
        ProductModel(
            id=product_id,
            monthly_fee_in_euros=Decimal("9.99"),
            name="Product 1",
            status="published",
        ),
        UserModel(id=user_id, email="user@example.com"),
        SubscriptionModel(
            id=uuid7(),
            is_active=True,
            product_id=product_id,
            user_id=user_id,
        ),
    )

    async with session.begin():
        session.add_all(models)
        await session.flush()

    async with session.begin():
        user_model = await session.get(UserModel, user_id)
        assert user_model is not None
        await session.delete(user_model)

    user_id_scalars = await session.scalars(select(SubscriptionModel.user_id))
    user_ids = user_id_scalars.all()
    assert user_ids == []
