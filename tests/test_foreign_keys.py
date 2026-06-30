"""Tests for per-connection SQLite foreign key enforcement.

SQLite enforces foreign keys per connection, so `PRAGMA foreign_keys=ON` must be
applied to every pooled connection -- not just the one used to create the
tables. These tests use a request-scoped session (obtained through the `session`
fixture, which checks out its own connection from the pool) to confirm that
enforcement is active outside of table creation.
"""

from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid7

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.data_structures.models import (
    ProductModel,
    SubscriptionModel,
    UserModel,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import AsyncSession


async def _get_subscription_user_ids(session: AsyncSession) -> Sequence[UUID]:
    result = await session.execute(select(SubscriptionModel.user_id))
    return result.scalars().all()


async def test_foreign_keys_are_enforced_for_request_scoped_session(
    session: AsyncSession,
) -> None:
    """Inserting a subscription with a dangling user_id must be rejected.

    If `PRAGMA foreign_keys=ON` were not applied to the request-scoped
    connection, SQLite would silently accept the orphaned foreign key.
    """
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


async def test_on_delete_cascade_removes_subscriptions_for_request_scoped_session(
    session: AsyncSession,
) -> None:
    """Deleting a user cascades to its subscriptions when FKs are enforced.

    `subscription.user_id` declares `ON DELETE CASCADE`, which SQLite only
    honors when foreign keys are enabled on the connection performing the
    delete.
    """
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
        await session.delete(user)

    async with session.begin():
        remaining_user_ids = await _get_subscription_user_ids(session)
    assert remaining_user_ids == []
