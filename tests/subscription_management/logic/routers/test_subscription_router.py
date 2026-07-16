import dataclasses
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import uuid7

import pytest
from _router_test_helpers import (
    insert_products,
    insert_subscriptions,
    insert_users,
    select_subscriptions,
    sorted_by_id,
    to_subscription_json,
)
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

if TYPE_CHECKING:
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


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
    await insert_products(session, product)
    users = (
        User(id=uuid7(), email="user1@example.com"),
        User(id=uuid7(), email="user2@example.com"),
    )
    await insert_users(session, *users)
    subscription = SubscriptionWithUserIdAndProductId(
        id=uuid7(),
        is_active=True,
        user_id=users[0].id,
        product_id=product.id,
    )
    await insert_subscriptions(session, subscription)

    new_subscription = SubscriptionWithUserIdAndProductId(
        id=uuid7(),
        is_active=True,
        user_id=users[1].id,
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
    assert response.json() == to_subscription_json(new_subscription, product)

    subscriptions_in_database = await select_subscriptions(session)
    assert frozenset(subscriptions_in_database) == frozenset(
        (
            SubscriptionWithProduct(
                id=subscription.id, is_active=subscription.is_active, product=product
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
    await insert_products(session, product)
    user = User(id=uuid7(), email="user@example.com")
    await insert_users(session, user)

    response = await client.post(
        "/subscriptions/",
        json={
            "id": str(uuid7()),
            "is_active": True,
            "user_id": str(user.id),
            "product_id": str(product.id),
        },
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {
        "detail": f"Product with ID {product.id} is in {product_status} status."
    }

    subscriptions_in_database = await select_subscriptions(session)
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
    await insert_products(session, product)
    users = (
        User(id=uuid7(), email="user1@example.com"),
        User(id=uuid7(), email="user2@example.com"),
    )
    await insert_users(session, *users)
    subscription = SubscriptionWithUserIdAndProductId(
        id=uuid7(),
        is_active=True,
        user_id=users[0].id,
        product_id=product.id,
    )
    await insert_subscriptions(session, subscription)

    response = await client.post(
        "/subscriptions/",
        json={
            "id": str(subscription.id),
            "is_active": False,
            "user_id": str(users[1].id),
            "product_id": str(product.id),
        },
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {
        "detail": f"Subscription with ID {subscription.id} already exists."
    }

    subscriptions_in_database = await select_subscriptions(session)
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
    await insert_products(session, product)
    user = User(id=uuid7(), email="user@example.com")
    await insert_users(session, user)

    nonexistent_user_id = uuid7()
    response = await client.post(
        "/subscriptions/",
        json={
            "id": str(uuid7()),
            "is_active": True,
            "user_id": str(nonexistent_user_id),
            "product_id": str(product.id),
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"User with ID {nonexistent_user_id} does not exist."
    }

    subscriptions_in_database = await select_subscriptions(session)
    assert subscriptions_in_database == ()


async def test_create_subscription_with_nonexistent_product_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    user = User(id=uuid7(), email="user@example.com")
    await insert_users(session, user)

    nonexistent_product_id = uuid7()
    response = await client.post(
        "/subscriptions/",
        json={
            "id": str(uuid7()),
            "is_active": True,
            "user_id": str(user.id),
            "product_id": str(nonexistent_product_id),
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"Product with ID {nonexistent_product_id} does not exist."
    }

    subscriptions_in_database = await select_subscriptions(session)
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
    await insert_products(session, product)
    users = (
        User(id=uuid7(), email="user1@example.com"),
        User(id=uuid7(), email="user2@example.com"),
    )
    await insert_users(session, *users)
    subscriptions = (
        SubscriptionWithUserIdAndProductId(
            id=uuid7(),
            is_active=True,
            user_id=users[0].id,
            product_id=product.id,
        ),
        SubscriptionWithUserIdAndProductId(
            id=uuid7(),
            is_active=False,
            user_id=users[1].id,
            product_id=product.id,
        ),
    )
    await insert_subscriptions(session, *subscriptions)

    response = await client.delete(f"/subscriptions/{subscriptions[0].id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.content == b""

    subscriptions_in_database = await select_subscriptions(session)
    assert subscriptions_in_database == (
        SubscriptionWithProduct(
            id=subscriptions[1].id,
            is_active=subscriptions[1].is_active,
            product=product,
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
    await insert_products(session, product)
    user = User(id=uuid7(), email="user@example.com")
    await insert_users(session, user)
    subscription = SubscriptionWithUserIdAndProductId(
        id=uuid7(),
        is_active=True,
        user_id=user.id,
        product_id=product.id,
    )
    await insert_subscriptions(session, subscription)

    nonexistent_subscription_id = uuid7()
    response = await client.delete(f"/subscriptions/{nonexistent_subscription_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"Subscription with ID {nonexistent_subscription_id} does not exist."
    }

    subscriptions_in_database = await select_subscriptions(session)
    assert subscriptions_in_database == (
        SubscriptionWithProduct(
            id=subscription.id, is_active=subscription.is_active, product=product
        ),
    )


async def test_read_subscriptions_returns_all_subscriptions(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    products = (
        Product(
            id=uuid7(),
            monthly_fee_in_euros=Decimal("9.99"),
            name="Product 1",
            status="published",
        ),
        Product(
            id=uuid7(),
            monthly_fee_in_euros=Decimal("19.99"),
            name="Product 2",
            status="published",
        ),
    )
    await insert_products(session, *products)
    users = (
        User(id=uuid7(), email="user1@example.com"),
        User(id=uuid7(), email="user2@example.com"),
    )
    await insert_users(session, *users)
    subscriptions = (
        SubscriptionWithUserIdAndProductId(
            id=uuid7(),
            is_active=True,
            user_id=users[0].id,
            product_id=products[0].id,
        ),
        SubscriptionWithUserIdAndProductId(
            id=uuid7(),
            is_active=False,
            user_id=users[1].id,
            product_id=products[1].id,
        ),
    )
    await insert_subscriptions(session, *subscriptions)

    response = await client.get("/subscriptions/")

    assert response.status_code == status.HTTP_200_OK
    assert sorted_by_id(response.json()) == sorted_by_id(
        (
            to_subscription_json(subscriptions[0], products[0]),
            to_subscription_json(subscriptions[1], products[1]),
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
    await insert_products(session, product)
    user = User(id=uuid7(), email="user@example.com")
    await insert_users(session, user)
    subscription = SubscriptionWithUserIdAndProductId(
        id=uuid7(),
        is_active=True,
        user_id=user.id,
        product_id=product.id,
    )
    await insert_subscriptions(session, subscription)

    response = await client.get(f"/subscriptions/{subscription.id}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == to_subscription_json(subscription, product)


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
    products = (
        Product(
            id=uuid7(),
            monthly_fee_in_euros=Decimal("9.99"),
            name="Product 1",
            status="published",
        ),
        Product(
            id=uuid7(),
            monthly_fee_in_euros=Decimal("19.99"),
            name="Product 2",
            status="published",
        ),
    )
    await insert_products(session, *products)
    users = (
        User(id=uuid7(), email="user1@example.com"),
        User(id=uuid7(), email="user2@example.com"),
    )
    await insert_users(session, *users)
    subscription = SubscriptionWithUserIdAndProductId(
        id=uuid7(),
        is_active=True,
        user_id=users[0].id,
        product_id=products[0].id,
    )
    await insert_subscriptions(session, subscription)

    response = await client.put(
        f"/subscriptions/{subscription.id}",
        json={
            "is_active": False,
            "user_id": str(users[1].id),
            "product_id": str(products[1].id),
        },
    )

    assert response.status_code == status.HTTP_200_OK
    updated_subscription = dataclasses.replace(
        subscription,
        is_active=False,
        user_id=users[1].id,
        product_id=products[1].id,
    )
    assert response.json() == to_subscription_json(updated_subscription, products[1])

    subscriptions_in_database = await select_subscriptions(session)
    assert subscriptions_in_database == (
        SubscriptionWithProduct(
            id=updated_subscription.id,
            is_active=updated_subscription.is_active,
            product=products[1],
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
    await insert_products(session, published_product, non_published_product)
    user = User(id=uuid7(), email="user@example.com")
    await insert_users(session, user)
    subscription = SubscriptionWithUserIdAndProductId(
        id=uuid7(),
        is_active=True,
        user_id=user.id,
        product_id=published_product.id,
    )
    await insert_subscriptions(session, subscription)

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

    subscriptions_in_database = await select_subscriptions(session)
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
    await insert_products(session, product)
    user = User(id=uuid7(), email="user@example.com")
    await insert_users(session, user)
    subscription = SubscriptionWithUserIdAndProductId(
        id=uuid7(),
        is_active=True,
        user_id=user.id,
        product_id=product.id,
    )
    await insert_subscriptions(session, subscription)

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

    subscriptions_in_database = await select_subscriptions(session)
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
    await insert_products(session, product)
    user = User(id=uuid7(), email="user@example.com")
    await insert_users(session, user)
    subscription = SubscriptionWithUserIdAndProductId(
        id=uuid7(),
        is_active=True,
        user_id=user.id,
        product_id=product.id,
    )
    await insert_subscriptions(session, subscription)

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

    subscriptions_in_database = await select_subscriptions(session)
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
    await insert_products(session, product)
    user = User(id=uuid7(), email="user@example.com")
    await insert_users(session, user)
    subscription = SubscriptionWithUserIdAndProductId(
        id=uuid7(),
        is_active=True,
        user_id=user.id,
        product_id=product.id,
    )
    await insert_subscriptions(session, subscription)

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

    subscriptions_in_database = await select_subscriptions(session)
    assert subscriptions_in_database == (
        SubscriptionWithProduct(
            id=subscription.id, is_active=subscription.is_active, product=product
        ),
    )
