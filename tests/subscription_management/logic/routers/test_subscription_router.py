import dataclasses
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import uuid7

import pytest
from fastapi import status

from subscription_management.data_structures.domain.product import (
    Product,
    ProductStatus,
)
from subscription_management.data_structures.domain.subscription import (
    SubscriptionWithProduct,
    SubscriptionWithUserIdAndProductId,
)
from subscription_management.data_structures.domain.user import User
from subscription_management.logic.repositories.product_repository import (
    ProductRepository,
)
from subscription_management.logic.repositories.subscription_repository import (
    SubscriptionRepository,
)
from subscription_management.logic.repositories.user_repository import (
    UserRepository,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession

type _JsonObject = dict[str, object]


def _get_id(json_object: _JsonObject) -> str:
    return str(json_object["id"])


def _get_subscription_repository(session: AsyncSession) -> SubscriptionRepository:
    return SubscriptionRepository(
        _session=session,
        _product_repository=ProductRepository(_session=session),
        _user_repository=UserRepository(_session=session),
    )


async def _insert_products(session: AsyncSession, *products: Product) -> None:
    async with session.begin():
        product_repository = ProductRepository(_session=session)
        for product in products:
            result = await product_repository.create_product(product)
            assert result[0] == "success", result


async def _insert_subscriptions(
    session: AsyncSession, *subscriptions: SubscriptionWithUserIdAndProductId
) -> None:
    async with session.begin():
        subscription_repository = _get_subscription_repository(session)
        for subscription in subscriptions:
            result = await subscription_repository.create_subscription(subscription)
            assert result[0] == "success", result


async def _insert_users(session: AsyncSession, *users: User) -> None:
    async with session.begin():
        user_repository = UserRepository(_session=session)
        for user in users:
            result = await user_repository.create_user(user)
            assert result[0] == "success", result


async def _select_subscriptions(
    session: AsyncSession,
) -> tuple[SubscriptionWithProduct, ...]:
    async with session.begin():
        subscription_repository = _get_subscription_repository(session)
        return await subscription_repository.read_subscriptions()


def _sorted_by_id(json_objects: Iterable[_JsonObject]) -> list[_JsonObject]:
    return sorted(json_objects, key=_get_id)


def _to_product_json(product: Product) -> _JsonObject:
    return {"id": str(product.id)} | _to_product_json_without_id(product)


def _to_product_json_without_id(product: Product) -> _JsonObject:
    return {
        "monthly_fee_in_euros": str(product.monthly_fee_in_euros),
        "name": product.name,
        "status": product.status,
    }


def _to_subscription_json(
    subscription: SubscriptionWithUserIdAndProductId, product: Product
) -> _JsonObject:
    return {
        "id": str(subscription.id),
        "is_active": subscription.is_active,
        "product": _to_product_json(product),
    }


async def test_create_subscription_adds_subscription_to_database(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    product = Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("9.99"),
        name="Product 1",
        status="published",
    )
    user1 = User(id=uuid7(), email="user1@example.com")
    user2 = User(id=uuid7(), email="user2@example.com")
    subscription1 = SubscriptionWithUserIdAndProductId(
        id=uuid7(),
        is_active=True,
        user_id=user1.id,
        product_id=product.id,
    )
    await _insert_products(session, product)
    await _insert_users(session, user1, user2)
    await _insert_subscriptions(session, subscription1)

    new_subscription = SubscriptionWithUserIdAndProductId(
        id=uuid7(),
        is_active=True,
        user_id=user2.id,
        product_id=product.id,
    )
    response = await client.post(
        "/subscriptions/",
        json={
            "id": str(new_subscription.id),
            "is_active": new_subscription.is_active,
            "user_id": str(new_subscription.user_id),
            "product_id": str(new_subscription.product_id),
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == _to_subscription_json(new_subscription, product)

    subscriptions_in_database = await _select_subscriptions(session)
    assert frozenset(subscriptions_in_database) == frozenset(
        (
            SubscriptionWithProduct(
                id=subscription1.id, is_active=subscription1.is_active, product=product
            ),
            SubscriptionWithProduct(
                id=new_subscription.id,
                is_active=new_subscription.is_active,
                product=product,
            ),
        )
    )


@pytest.mark.parametrize("product_status", ["draft", "deprecated"])
async def test_create_subscription_for_non_published_product_fails(
    client: AsyncClient,
    session: AsyncSession,
    product_status: ProductStatus,
) -> None:
    product = Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("9.99"),
        name="Product 1",
        status=product_status,
    )
    user = User(id=uuid7(), email="user@example.com")
    await _insert_products(session, product)
    await _insert_users(session, user)

    subscription_id = uuid7()
    response = await client.post(
        "/subscriptions/",
        json={
            "id": str(subscription_id),
            "is_active": True,
            "user_id": str(user.id),
            "product_id": str(product.id),
        },
    )
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {
        "detail": f"Product with ID {product.id} is in {product_status} status."
    }

    subscriptions_in_database = await _select_subscriptions(session)
    assert subscriptions_in_database == ()


async def test_create_subscription_with_existing_id_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    product = Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("9.99"),
        name="Product 1",
        status="published",
    )
    user1 = User(id=uuid7(), email="user1@example.com")
    user2 = User(id=uuid7(), email="user2@example.com")
    subscription = SubscriptionWithUserIdAndProductId(
        id=uuid7(),
        is_active=True,
        user_id=user1.id,
        product_id=product.id,
    )
    await _insert_products(session, product)
    await _insert_users(session, user1, user2)
    await _insert_subscriptions(session, subscription)

    response = await client.post(
        "/subscriptions/",
        json={
            "id": str(subscription.id),
            "is_active": False,
            "user_id": str(user2.id),
            "product_id": str(product.id),
        },
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {
        "detail": f"Subscription with ID {subscription.id} already exists."
    }

    subscriptions_in_database = await _select_subscriptions(session)
    assert subscriptions_in_database == (
        SubscriptionWithProduct(
            id=subscription.id, is_active=subscription.is_active, product=product
        ),
    )


async def test_create_subscription_with_nonexistent_user_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    product = Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("9.99"),
        name="Product 1",
        status="published",
    )
    user = User(id=uuid7(), email="user@example.com")
    await _insert_products(session, product)
    await _insert_users(session, user)

    subscription_id = uuid7()
    nonexistent_user_id = uuid7()
    response = await client.post(
        "/subscriptions/",
        json={
            "id": str(subscription_id),
            "is_active": True,
            "user_id": str(nonexistent_user_id),
            "product_id": str(product.id),
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"User with ID {nonexistent_user_id} does not exist."
    }

    subscriptions_in_database = await _select_subscriptions(session)
    assert subscriptions_in_database == ()


async def test_create_subscription_with_nonexistent_product_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    user = User(id=uuid7(), email="user@example.com")
    await _insert_users(session, user)

    subscription_id = uuid7()
    nonexistent_product_id = uuid7()
    response = await client.post(
        "/subscriptions/",
        json={
            "id": str(subscription_id),
            "is_active": True,
            "user_id": str(user.id),
            "product_id": str(nonexistent_product_id),
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"Product with ID {nonexistent_product_id} does not exist."
    }

    subscriptions_in_database = await _select_subscriptions(session)
    assert subscriptions_in_database == ()


async def test_delete_subscription_removes_subscription_from_database(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    product = Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("9.99"),
        name="Product 1",
        status="published",
    )
    user1 = User(id=uuid7(), email="user1@example.com")
    user2 = User(id=uuid7(), email="user2@example.com")
    subscription1 = SubscriptionWithUserIdAndProductId(
        id=uuid7(),
        is_active=True,
        user_id=user1.id,
        product_id=product.id,
    )
    subscription2 = SubscriptionWithUserIdAndProductId(
        id=uuid7(),
        is_active=False,
        user_id=user2.id,
        product_id=product.id,
    )
    await _insert_products(session, product)
    await _insert_users(session, user1, user2)
    await _insert_subscriptions(session, subscription1, subscription2)

    response = await client.delete(f"/subscriptions/{subscription1.id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.content == b""

    subscriptions_in_database = await _select_subscriptions(session)
    assert subscriptions_in_database == (
        SubscriptionWithProduct(
            id=subscription2.id, is_active=subscription2.is_active, product=product
        ),
    )


async def test_delete_subscription_with_nonexistent_id_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    product = Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("9.99"),
        name="Product 1",
        status="published",
    )
    user = User(id=uuid7(), email="user@example.com")
    subscription = SubscriptionWithUserIdAndProductId(
        id=uuid7(),
        is_active=True,
        user_id=user.id,
        product_id=product.id,
    )
    await _insert_products(session, product)
    await _insert_users(session, user)
    await _insert_subscriptions(session, subscription)

    nonexistent_subscription_id = uuid7()
    response = await client.delete(f"/subscriptions/{nonexistent_subscription_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"Subscription with ID {nonexistent_subscription_id} does not exist."
    }

    subscriptions_in_database = await _select_subscriptions(session)
    assert subscriptions_in_database == (
        SubscriptionWithProduct(
            id=subscription.id, is_active=subscription.is_active, product=product
        ),
    )


async def test_read_subscriptions_returns_all_subscriptions(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    product1 = Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("9.99"),
        name="Product 1",
        status="published",
    )
    product2 = Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("19.99"),
        name="Product 2",
        status="published",
    )
    user1 = User(id=uuid7(), email="user1@example.com")
    user2 = User(id=uuid7(), email="user2@example.com")
    subscription1 = SubscriptionWithUserIdAndProductId(
        id=uuid7(),
        is_active=True,
        user_id=user1.id,
        product_id=product1.id,
    )
    subscription2 = SubscriptionWithUserIdAndProductId(
        id=uuid7(),
        is_active=False,
        user_id=user2.id,
        product_id=product2.id,
    )
    await _insert_products(session, product1, product2)
    await _insert_users(session, user1, user2)
    await _insert_subscriptions(session, subscription1, subscription2)

    response = await client.get("/subscriptions/")

    assert response.status_code == status.HTTP_200_OK
    assert _sorted_by_id(response.json()) == _sorted_by_id(
        (
            _to_subscription_json(subscription1, product1),
            _to_subscription_json(subscription2, product2),
        )
    )


async def test_read_subscriptions_returns_empty_list_when_no_subscriptions(
    client: AsyncClient,
) -> None:
    response = await client.get("/subscriptions/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


async def test_read_subscription_by_id_returns_subscription(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    product = Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("9.99"),
        name="Product 1",
        status="published",
    )
    user = User(id=uuid7(), email="user@example.com")
    subscription = SubscriptionWithUserIdAndProductId(
        id=uuid7(),
        is_active=True,
        user_id=user.id,
        product_id=product.id,
    )
    await _insert_products(session, product)
    await _insert_users(session, user)
    await _insert_subscriptions(session, subscription)

    response = await client.get(f"/subscriptions/{subscription.id}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == _to_subscription_json(subscription, product)


async def test_read_subscription_by_id_returns_404_when_subscription_does_not_exist(
    client: AsyncClient,
) -> None:
    subscription_id = uuid7()

    response = await client.get(f"/subscriptions/{subscription_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"Subscription with ID {subscription_id} does not exist."
    }


async def test_update_subscription_updates_subscription_in_database(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    product1 = Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("9.99"),
        name="Product 1",
        status="published",
    )
    product2 = Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("19.99"),
        name="Product 2",
        status="published",
    )
    user1 = User(id=uuid7(), email="user1@example.com")
    user2 = User(id=uuid7(), email="user2@example.com")
    subscription = SubscriptionWithUserIdAndProductId(
        id=uuid7(),
        is_active=True,
        user_id=user1.id,
        product_id=product1.id,
    )
    await _insert_products(session, product1, product2)
    await _insert_users(session, user1, user2)
    await _insert_subscriptions(session, subscription)

    response = await client.put(
        f"/subscriptions/{subscription.id}",
        json={
            "is_active": False,
            "user_id": str(user2.id),
            "product_id": str(product2.id),
        },
    )

    assert response.status_code == status.HTTP_200_OK
    updated_subscription = dataclasses.replace(
        subscription,
        is_active=False,
        user_id=user2.id,
        product_id=product2.id,
    )
    assert response.json() == _to_subscription_json(updated_subscription, product2)

    subscriptions_in_database = await _select_subscriptions(session)
    assert subscriptions_in_database == (
        SubscriptionWithProduct(
            id=updated_subscription.id,
            is_active=updated_subscription.is_active,
            product=product2,
        ),
    )


@pytest.mark.parametrize("product_status", ["draft", "deprecated"])
async def test_update_subscription_to_non_published_product_fails(
    client: AsyncClient,
    session: AsyncSession,
    product_status: ProductStatus,
) -> None:
    published_product = Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("9.99"),
        name="Published Product",
        status="published",
    )
    non_published_product = Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("19.99"),
        name="Non-Published Product",
        status=product_status,
    )
    user = User(id=uuid7(), email="user@example.com")
    subscription = SubscriptionWithUserIdAndProductId(
        id=uuid7(),
        is_active=True,
        user_id=user.id,
        product_id=published_product.id,
    )
    await _insert_products(session, published_product, non_published_product)
    await _insert_users(session, user)
    await _insert_subscriptions(session, subscription)

    response = await client.put(
        f"/subscriptions/{subscription.id}",
        json={
            "is_active": False,
            "user_id": str(user.id),
            "product_id": str(non_published_product.id),
        },
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {
        "detail": (
            f"Product with ID {non_published_product.id} is in {product_status} status."
        )
    }

    subscriptions_in_database = await _select_subscriptions(session)
    assert subscriptions_in_database == (
        SubscriptionWithProduct(
            id=subscription.id,
            is_active=subscription.is_active,
            product=published_product,
        ),
    )


async def test_update_subscription_with_nonexistent_id_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    product = Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("9.99"),
        name="Product 1",
        status="published",
    )
    user = User(id=uuid7(), email="user@example.com")
    subscription = SubscriptionWithUserIdAndProductId(
        id=uuid7(),
        is_active=True,
        user_id=user.id,
        product_id=product.id,
    )
    await _insert_products(session, product)
    await _insert_users(session, user)
    await _insert_subscriptions(session, subscription)

    nonexistent_subscription_id = uuid7()
    response = await client.put(
        f"/subscriptions/{nonexistent_subscription_id}",
        json={
            "is_active": False,
            "user_id": str(user.id),
            "product_id": str(product.id),
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"Subscription with ID {nonexistent_subscription_id} does not exist."
    }

    subscriptions_in_database = await _select_subscriptions(session)
    assert subscriptions_in_database == (
        SubscriptionWithProduct(
            id=subscription.id, is_active=subscription.is_active, product=product
        ),
    )


async def test_update_subscription_with_nonexistent_user_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    product = Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("9.99"),
        name="Product 1",
        status="published",
    )
    user = User(id=uuid7(), email="user@example.com")
    subscription = SubscriptionWithUserIdAndProductId(
        id=uuid7(),
        is_active=True,
        user_id=user.id,
        product_id=product.id,
    )
    await _insert_products(session, product)
    await _insert_users(session, user)
    await _insert_subscriptions(session, subscription)

    nonexistent_user_id = uuid7()
    response = await client.put(
        f"/subscriptions/{subscription.id}",
        json={
            "is_active": False,
            "user_id": str(nonexistent_user_id),
            "product_id": str(product.id),
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"User with ID {nonexistent_user_id} does not exist."
    }

    subscriptions_in_database = await _select_subscriptions(session)
    assert subscriptions_in_database == (
        SubscriptionWithProduct(
            id=subscription.id, is_active=subscription.is_active, product=product
        ),
    )


async def test_update_subscription_with_nonexistent_product_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    product = Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("9.99"),
        name="Product 1",
        status="published",
    )
    user = User(id=uuid7(), email="user@example.com")
    subscription = SubscriptionWithUserIdAndProductId(
        id=uuid7(),
        is_active=True,
        user_id=user.id,
        product_id=product.id,
    )
    await _insert_products(session, product)
    await _insert_users(session, user)
    await _insert_subscriptions(session, subscription)

    nonexistent_product_id = uuid7()
    response = await client.put(
        f"/subscriptions/{subscription.id}",
        json={
            "is_active": False,
            "user_id": str(user.id),
            "product_id": str(nonexistent_product_id),
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"Product with ID {nonexistent_product_id} does not exist."
    }

    subscriptions_in_database = await _select_subscriptions(session)
    assert subscriptions_in_database == (
        SubscriptionWithProduct(
            id=subscription.id, is_active=subscription.is_active, product=product
        ),
    )
