import functools
from collections.abc import Awaitable, Callable, Iterable, Mapping, Sequence
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

import pytest
from sqlalchemy import select

from subscription_management.data_structures.domain.product import ProductStatus
from subscription_management.data_structures.models import (
    ProductModel,
    SubscriptionModel,
    UserModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


type AddProductsToDatabase = Callable[[*tuple[ProductTuple, ...]], Awaitable[None]]
type AddSubscriptionsToDatabase = Callable[
    [*tuple[SubscriptionTuple, ...]], Awaitable[None]
]
type AddUsersToDatabase = Callable[[*tuple[UserTuple, ...]], Awaitable[None]]
type ProductTuple = tuple[UUID, Decimal, str, ProductStatus]
type StrMapping = Mapping[str, object]
type SubscriptionTuple = tuple[UUID, bool, UUID, UUID]
type UserTuple = tuple[UUID, str]


def _get_id(d: StrMapping) -> str:
    return str(d["id"])


async def _add_products_to_database(
    session: AsyncSession, *products: ProductTuple
) -> None:
    async with session.begin():
        session.add_all(ProductModel(*product) for product in products)


async def _add_subscriptions_to_database(
    session: AsyncSession, *subscriptions: SubscriptionTuple
) -> None:
    async with session.begin():
        session.add_all(
            SubscriptionModel(*subscription) for subscription in subscriptions
        )


async def _add_users_to_database(session: AsyncSession, *users: UserTuple) -> None:
    async with session.begin():
        session.add_all(UserModel(*user) for user in users)


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
def add_products_to_database(session: AsyncSession) -> AddProductsToDatabase:
    return functools.partial(_add_products_to_database, session)


@pytest.fixture
def add_subscriptions_to_database(
    session: AsyncSession,
) -> AddSubscriptionsToDatabase:
    return functools.partial(_add_subscriptions_to_database, session)


@pytest.fixture
def add_users_to_database(session: AsyncSession) -> AddUsersToDatabase:
    return functools.partial(_add_users_to_database, session)


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
