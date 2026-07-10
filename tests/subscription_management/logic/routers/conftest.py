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
    from decimal import Decimal
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

    from subscription_management.data_structures.domain.product import ProductStatus

type ProductTuple = tuple[UUID, Decimal, str, ProductStatus]
type StrDict = dict[str, object]
type SubscriptionTuple = tuple[UUID, bool, UUID, UUID]
type UserTuple = tuple[UUID, str]


def _get_id(d: StrDict) -> str:
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


def _sorted_by_id(ds: Iterable[StrDict]) -> list[StrDict]:
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
def sorted_by_id() -> Callable[[Iterable[StrDict]], list[StrDict]]:
    return _sorted_by_id
