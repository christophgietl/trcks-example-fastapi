import functools
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import select

from subscription_management.data_structures.models import (
    ProductModel,
    SubscriptionModel,
    UserModel,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Iterable, Sequence

    from sqlalchemy.ext.asyncio import AsyncSession

    from ._types import ProductTuple, StrMapping, SubscriptionTuple, UserTuple


def _get_id(d: StrMapping) -> str:
    return str(d["id"])


async def _get_products_from_database(
    session: AsyncSession,
) -> Sequence[ProductTuple]:
    statement = select(
        ProductModel.id,
        ProductModel.monthly_fee_in_euros,
        ProductModel.name,
        ProductModel.status,
    )
    async with session.begin():
        result = await session.execute(statement)
        return result.tuples().all()


async def _get_subscriptions_from_database(
    session: AsyncSession,
) -> Sequence[SubscriptionTuple]:
    statement = select(
        SubscriptionModel.id,
        SubscriptionModel.is_active,
        SubscriptionModel.user_id,
        SubscriptionModel.product_id,
    )
    async with session.begin():
        result = await session.execute(statement)
        return result.tuples().all()


async def _get_users_from_database(
    session: AsyncSession,
) -> Sequence[UserTuple]:
    statement = select(UserModel.id, UserModel.email)
    async with session.begin():
        result = await session.execute(statement)
        return result.tuples().all()


def _sorted_by_id(ds: Iterable[StrMapping]) -> list[StrMapping]:
    return sorted(ds, key=_get_id)


@pytest.fixture
def get_products_from_database(
    session: AsyncSession,
) -> Callable[[], Awaitable[Sequence[ProductTuple]]]:
    return functools.partial(_get_products_from_database, session)


@pytest.fixture
def get_subscriptions_from_database(
    session: AsyncSession,
) -> Callable[[], Awaitable[Sequence[SubscriptionTuple]]]:
    return functools.partial(_get_subscriptions_from_database, session)


@pytest.fixture
def get_users_from_database(
    session: AsyncSession,
) -> Callable[[], Awaitable[Sequence[UserTuple]]]:
    return functools.partial(_get_users_from_database, session)


@pytest.fixture
def sorted_by_id() -> Callable[[Iterable[StrMapping]], list[StrMapping]]:
    return _sorted_by_id
