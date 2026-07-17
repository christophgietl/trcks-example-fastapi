"""Testing helper module as recommended by the pytest documentation.

See Also:
    https://docs.pytest.org/en/9.0.x/explanation/pythonpath.html#import-modes
"""

from typing import TYPE_CHECKING

from subscription_management.logic.repositories.product_repository import (
    ProductRepository,
)
from subscription_management.logic.repositories.subscription_repository import (
    SubscriptionRepository,
)
from subscription_management.logic.repositories.user_repository import UserRepository

if TYPE_CHECKING:
    from collections.abc import Iterable

    from sqlalchemy.ext.asyncio import AsyncSession

    from subscription_management.data_structures.domain.product import Product
    from subscription_management.data_structures.domain.subscription import (
        SubscriptionWithProduct,
        SubscriptionWithUserIdAndProductId,
    )
    from subscription_management.data_structures.domain.user import (
        User,
        UserWithSubscriptionsWithProducts,
    )

__docformat__ = "google"

type _JsonObject = dict[str, object]


def _get_id(json_object: _JsonObject) -> str:
    return str(json_object["id"])


def _get_subscription_repository(session: AsyncSession) -> SubscriptionRepository:
    return SubscriptionRepository(
        _session=session,
        _product_repository=ProductRepository(_session=session),
        _user_repository=UserRepository(_session=session),
    )


async def insert_products(session: AsyncSession, *products: Product) -> None:
    async with session.begin():
        product_repository = ProductRepository(_session=session)
        for product in products:
            result = await product_repository.create_product(product)
            assert result[0] == "success", result


async def insert_subscriptions(
    session: AsyncSession, *subscriptions: SubscriptionWithUserIdAndProductId
) -> None:
    async with session.begin():
        subscription_repository = _get_subscription_repository(session)
        for subscription in subscriptions:
            result = await subscription_repository.create_subscription(subscription)
            assert result[0] == "success", result


async def insert_users(session: AsyncSession, *users: User) -> None:
    async with session.begin():
        user_repository = UserRepository(_session=session)
        for user in users:
            result = await user_repository.create_user(user)
            assert result[0] == "success", result


async def select_products(session: AsyncSession) -> tuple[Product, ...]:
    async with session.begin():
        product_repository = ProductRepository(_session=session)
        return await product_repository.read_products()


async def select_subscriptions(
    session: AsyncSession,
) -> tuple[SubscriptionWithProduct, ...]:
    async with session.begin():
        subscription_repository = _get_subscription_repository(session)
        return await subscription_repository.read_subscriptions()


async def select_users(
    session: AsyncSession,
) -> tuple[UserWithSubscriptionsWithProducts, ...]:
    async with session.begin():
        user_repository = UserRepository(_session=session)
        return await user_repository.read_users()


def sorted_by_id(json_objects: Iterable[_JsonObject]) -> list[_JsonObject]:
    return sorted(json_objects, key=_get_id)


def to_product_json_without_id(product: Product) -> _JsonObject:
    return {
        "monthly_fee_in_euros": str(product.monthly_fee_in_euros),
        "name": product.name,
        "status": product.status,
    }


def to_product_json(product: Product) -> _JsonObject:
    return {"id": str(product.id)} | to_product_json_without_id(product)


def to_subscription_create_json(
    subscription: SubscriptionWithUserIdAndProductId,
) -> _JsonObject:
    return {
        "id": str(subscription.id),
        "is_active": subscription.is_active,
        "user_id": str(subscription.user_id),
        "product_id": str(subscription.product_id),
    }


def to_subscription_json(
    subscription: SubscriptionWithUserIdAndProductId, product: Product
) -> _JsonObject:
    return {
        "id": str(subscription.id),
        "is_active": subscription.is_active,
        "product": to_product_json(product),
    }


def to_subscription_update_json(
    subscription: SubscriptionWithUserIdAndProductId,
) -> _JsonObject:
    return {
        "is_active": subscription.is_active,
        "user_id": str(subscription.user_id),
        "product_id": str(subscription.product_id),
    }


def to_subscription_with_product_json(
    subscription: SubscriptionWithProduct,
) -> _JsonObject:
    return {
        "id": str(subscription.id),
        "is_active": subscription.is_active,
        "product": to_product_json(subscription.product),
    }


def to_user_json(user: User) -> _JsonObject:
    return {"id": str(user.id), "email": user.email}


def to_user_with_subscriptions_with_products_json(
    user: UserWithSubscriptionsWithProducts,
) -> _JsonObject:
    return {
        "id": str(user.id),
        "email": user.email,
        "subscriptions": [
            to_subscription_with_product_json(subscription)
            for subscription in user.subscriptions_with_products
        ],
    }
