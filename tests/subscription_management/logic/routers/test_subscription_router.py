from collections.abc import Awaitable, Callable, Iterable, Mapping, Sequence
from decimal import Decimal
from typing import TYPE_CHECKING, Literal
from uuid import UUID, uuid7

import pytest
from fastapi import status

from subscription_management.data_structures.domain.product import ProductStatus

if TYPE_CHECKING:
    from httpx import AsyncClient

type AddProductsToDatabase = Callable[[*tuple[ProductTuple, ...]], Awaitable[None]]
type AddSubscriptionsToDatabase = Callable[
    [*tuple[SubscriptionTuple, ...]], Awaitable[None]
]
type AddUsersToDatabase = Callable[[*tuple[UserTuple, ...]], Awaitable[None]]
type GetSubscriptionsFromDatabase = Callable[[], Awaitable[Sequence[SubscriptionTuple]]]
type ProductTuple = tuple[UUID, Decimal, str, ProductStatus]
type SortedById = Callable[[Iterable[StrMapping]], list[StrMapping]]
type StrMapping = Mapping[str, object]
type SubscriptionTuple = tuple[UUID, bool, UUID, UUID]
type UserTuple = tuple[UUID, str]


def _to_json(
    subscription: SubscriptionTuple, product: ProductTuple
) -> dict[str, object]:
    return {
        "id": str(subscription[0]),
        "is_active": subscription[1],
        "product": {
            "id": str(product[0]),
            "monthly_fee_in_euros": str(product[1]),
            "name": product[2],
            "status": product[3],
        },
    }


async def test_create_subscription_adds_subscription_to_database(
    client: AsyncClient,
    add_products_to_database: AddProductsToDatabase,
    add_subscriptions_to_database: AddSubscriptionsToDatabase,
    add_users_to_database: AddUsersToDatabase,
    get_subscriptions_from_database: GetSubscriptionsFromDatabase,
) -> None:
    product: ProductTuple = (uuid7(), Decimal("9.99"), "Product 1", "published")
    user1: UserTuple = (uuid7(), "user1@example.com")
    user2: UserTuple = (uuid7(), "user2@example.com")
    subscription1: SubscriptionTuple = (uuid7(), True, user1[0], product[0])
    await add_products_to_database(product)
    await add_users_to_database(user1, user2)
    await add_subscriptions_to_database(subscription1)

    new_subscription: SubscriptionTuple = (uuid7(), True, user2[0], product[0])
    response = await client.post(
        "/subscriptions/",
        json={
            "id": str(new_subscription[0]),
            "is_active": new_subscription[1],
            "user_id": str(new_subscription[2]),
            "product_id": str(new_subscription[3]),
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == _to_json(new_subscription, product)

    subscriptions_in_database = await get_subscriptions_from_database()
    assert sorted(subscriptions_in_database) == sorted(
        (subscription1, new_subscription)
    )


@pytest.mark.parametrize("product_status", ["draft", "deprecated"])
async def test_create_subscription_for_non_published_product_fails(
    client: AsyncClient,
    add_products_to_database: AddProductsToDatabase,
    add_users_to_database: AddUsersToDatabase,
    get_subscriptions_from_database: GetSubscriptionsFromDatabase,
    product_status: Literal["draft", "deprecated"],
) -> None:
    product: ProductTuple = (uuid7(), Decimal("9.99"), "Product 1", product_status)
    user: UserTuple = (uuid7(), "user@example.com")
    await add_products_to_database(product)
    await add_users_to_database(user)

    subscription_id = uuid7()
    response = await client.post(
        "/subscriptions/",
        json={
            "id": str(subscription_id),
            "is_active": True,
            "user_id": str(user[0]),
            "product_id": str(product[0]),
        },
    )
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {
        "detail": f"Product with ID {product[0]} is in {product_status} status."
    }

    subscriptions_in_database = await get_subscriptions_from_database()
    assert subscriptions_in_database == []


async def test_create_subscription_with_existing_id_fails(
    client: AsyncClient,
    add_products_to_database: AddProductsToDatabase,
    add_subscriptions_to_database: AddSubscriptionsToDatabase,
    add_users_to_database: AddUsersToDatabase,
    get_subscriptions_from_database: GetSubscriptionsFromDatabase,
) -> None:
    product: ProductTuple = (uuid7(), Decimal("9.99"), "Product 1", "published")
    user1: UserTuple = (uuid7(), "user1@example.com")
    user2: UserTuple = (uuid7(), "user2@example.com")
    subscription: SubscriptionTuple = (uuid7(), True, user1[0], product[0])
    await add_products_to_database(product)
    await add_users_to_database(user1, user2)
    await add_subscriptions_to_database(subscription)

    response = await client.post(
        "/subscriptions/",
        json={
            "id": str(subscription[0]),
            "is_active": False,
            "user_id": str(user2[0]),
            "product_id": str(product[0]),
        },
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {
        "detail": f"Subscription with ID {subscription[0]} already exists."
    }

    subscriptions_in_database = await get_subscriptions_from_database()
    assert subscriptions_in_database == [subscription]


async def test_create_subscription_with_nonexistent_user_fails(
    client: AsyncClient,
    add_products_to_database: AddProductsToDatabase,
    add_users_to_database: AddUsersToDatabase,
    get_subscriptions_from_database: GetSubscriptionsFromDatabase,
) -> None:
    product: ProductTuple = (uuid7(), Decimal("9.99"), "Product 1", "published")
    user: UserTuple = (uuid7(), "user@example.com")
    await add_products_to_database(product)
    await add_users_to_database(user)

    subscription_id = uuid7()
    nonexistent_user_id = uuid7()
    response = await client.post(
        "/subscriptions/",
        json={
            "id": str(subscription_id),
            "is_active": True,
            "user_id": str(nonexistent_user_id),
            "product_id": str(product[0]),
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"User with ID {nonexistent_user_id} does not exist."
    }

    subscriptions_in_database = await get_subscriptions_from_database()
    assert subscriptions_in_database == []


async def test_create_subscription_with_nonexistent_product_fails(
    client: AsyncClient,
    add_users_to_database: AddUsersToDatabase,
    get_subscriptions_from_database: GetSubscriptionsFromDatabase,
) -> None:
    user: UserTuple = (uuid7(), "user@example.com")
    await add_users_to_database(user)

    subscription_id = uuid7()
    nonexistent_product_id = uuid7()
    response = await client.post(
        "/subscriptions/",
        json={
            "id": str(subscription_id),
            "is_active": True,
            "user_id": str(user[0]),
            "product_id": str(nonexistent_product_id),
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"Product with ID {nonexistent_product_id} does not exist."
    }

    subscriptions_in_database = await get_subscriptions_from_database()
    assert subscriptions_in_database == []


async def test_delete_subscription_removes_subscription_from_database(
    client: AsyncClient,
    add_products_to_database: AddProductsToDatabase,
    add_subscriptions_to_database: AddSubscriptionsToDatabase,
    add_users_to_database: AddUsersToDatabase,
    get_subscriptions_from_database: GetSubscriptionsFromDatabase,
) -> None:
    product: ProductTuple = (uuid7(), Decimal("9.99"), "Product 1", "published")
    user1: UserTuple = (uuid7(), "user1@example.com")
    user2: UserTuple = (uuid7(), "user2@example.com")
    subscription1: SubscriptionTuple = (uuid7(), True, user1[0], product[0])
    subscription2: SubscriptionTuple = (uuid7(), False, user2[0], product[0])
    await add_products_to_database(product)
    await add_users_to_database(user1, user2)
    await add_subscriptions_to_database(subscription1, subscription2)

    response = await client.delete(f"/subscriptions/{subscription1[0]}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.content == b""

    subscriptions_in_database = await get_subscriptions_from_database()
    assert subscriptions_in_database == [subscription2]


async def test_delete_subscription_with_nonexistent_id_fails(
    client: AsyncClient,
    add_products_to_database: AddProductsToDatabase,
    add_subscriptions_to_database: AddSubscriptionsToDatabase,
    add_users_to_database: AddUsersToDatabase,
    get_subscriptions_from_database: GetSubscriptionsFromDatabase,
) -> None:
    product: ProductTuple = (uuid7(), Decimal("9.99"), "Product 1", "published")
    user: UserTuple = (uuid7(), "user@example.com")
    subscription: SubscriptionTuple = (uuid7(), True, user[0], product[0])
    await add_products_to_database(product)
    await add_users_to_database(user)
    await add_subscriptions_to_database(subscription)

    nonexistent_subscription_id = uuid7()
    response = await client.delete(f"/subscriptions/{nonexistent_subscription_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"Subscription with ID {nonexistent_subscription_id} does not exist."
    }

    subscriptions_in_database = await get_subscriptions_from_database()
    assert subscriptions_in_database == [subscription]


async def test_read_subscriptions_returns_all_subscriptions(
    client: AsyncClient,
    add_products_to_database: AddProductsToDatabase,
    add_subscriptions_to_database: AddSubscriptionsToDatabase,
    add_users_to_database: AddUsersToDatabase,
    sorted_by_id: SortedById,
) -> None:
    product1: ProductTuple = (uuid7(), Decimal("9.99"), "Product 1", "published")
    product2: ProductTuple = (uuid7(), Decimal("19.99"), "Product 2", "published")
    user1: UserTuple = (uuid7(), "user1@example.com")
    user2: UserTuple = (uuid7(), "user2@example.com")
    subscription1: SubscriptionTuple = (uuid7(), True, user1[0], product1[0])
    subscription2: SubscriptionTuple = (uuid7(), False, user2[0], product2[0])
    await add_products_to_database(product1, product2)
    await add_users_to_database(user1, user2)
    await add_subscriptions_to_database(subscription1, subscription2)

    response = await client.get("/subscriptions/")

    assert response.status_code == status.HTTP_200_OK
    assert sorted_by_id(response.json()) == sorted_by_id(
        (
            _to_json(subscription1, product1),
            _to_json(subscription2, product2),
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
    add_products_to_database: AddProductsToDatabase,
    add_subscriptions_to_database: AddSubscriptionsToDatabase,
    add_users_to_database: AddUsersToDatabase,
) -> None:
    product: ProductTuple = (uuid7(), Decimal("9.99"), "Product 1", "published")
    user: UserTuple = (uuid7(), "user@example.com")
    subscription: SubscriptionTuple = (uuid7(), True, user[0], product[0])
    await add_products_to_database(product)
    await add_users_to_database(user)
    await add_subscriptions_to_database(subscription)

    response = await client.get(f"/subscriptions/{subscription[0]}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == _to_json(subscription, product)


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
    add_products_to_database: AddProductsToDatabase,
    add_subscriptions_to_database: AddSubscriptionsToDatabase,
    add_users_to_database: AddUsersToDatabase,
    get_subscriptions_from_database: GetSubscriptionsFromDatabase,
) -> None:
    product1: ProductTuple = (uuid7(), Decimal("9.99"), "Product 1", "published")
    product2: ProductTuple = (uuid7(), Decimal("19.99"), "Product 2", "published")
    user1: UserTuple = (uuid7(), "user1@example.com")
    user2: UserTuple = (uuid7(), "user2@example.com")
    subscription: SubscriptionTuple = (uuid7(), True, user1[0], product1[0])
    await add_products_to_database(product1, product2)
    await add_users_to_database(user1, user2)
    await add_subscriptions_to_database(subscription)

    response = await client.put(
        f"/subscriptions/{subscription[0]}",
        json={
            "is_active": False,
            "user_id": str(user2[0]),
            "product_id": str(product2[0]),
        },
    )

    assert response.status_code == status.HTTP_200_OK
    updated_subscription: SubscriptionTuple = (
        subscription[0],
        False,
        user2[0],
        product2[0],
    )
    assert response.json() == _to_json(updated_subscription, product2)

    subscriptions_in_database = await get_subscriptions_from_database()
    assert subscriptions_in_database == [updated_subscription]


@pytest.mark.parametrize("product_status", ["draft", "deprecated"])
async def test_update_subscription_to_non_published_product_fails(  # noqa: PLR0913
    client: AsyncClient,
    add_products_to_database: AddProductsToDatabase,
    add_subscriptions_to_database: AddSubscriptionsToDatabase,
    add_users_to_database: AddUsersToDatabase,
    get_subscriptions_from_database: GetSubscriptionsFromDatabase,
    product_status: Literal["draft", "deprecated"],
) -> None:
    published_product: ProductTuple = (
        uuid7(),
        Decimal("9.99"),
        "Published Product",
        "published",
    )
    non_published_product: ProductTuple = (
        uuid7(),
        Decimal("19.99"),
        "Non-Published Product",
        product_status,
    )
    user: UserTuple = (uuid7(), "user@example.com")
    subscription: SubscriptionTuple = (
        uuid7(),
        True,
        user[0],
        published_product[0],
    )
    await add_products_to_database(published_product, non_published_product)
    await add_users_to_database(user)
    await add_subscriptions_to_database(subscription)

    response = await client.put(
        f"/subscriptions/{subscription[0]}",
        json={
            "is_active": False,
            "user_id": str(user[0]),
            "product_id": str(non_published_product[0]),
        },
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {
        "detail": (
            f"Product with ID {non_published_product[0]} is in {product_status} status."
        )
    }

    subscriptions_in_database = await get_subscriptions_from_database()
    assert subscriptions_in_database == [subscription]


async def test_update_subscription_with_nonexistent_id_fails(
    client: AsyncClient,
    add_products_to_database: AddProductsToDatabase,
    add_subscriptions_to_database: AddSubscriptionsToDatabase,
    add_users_to_database: AddUsersToDatabase,
    get_subscriptions_from_database: GetSubscriptionsFromDatabase,
) -> None:
    product: ProductTuple = (uuid7(), Decimal("9.99"), "Product 1", "published")
    user: UserTuple = (uuid7(), "user@example.com")
    subscription: SubscriptionTuple = (uuid7(), True, user[0], product[0])
    await add_products_to_database(product)
    await add_users_to_database(user)
    await add_subscriptions_to_database(subscription)

    nonexistent_subscription_id = uuid7()
    response = await client.put(
        f"/subscriptions/{nonexistent_subscription_id}",
        json={
            "is_active": False,
            "user_id": str(user[0]),
            "product_id": str(product[0]),
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"Subscription with ID {nonexistent_subscription_id} does not exist."
    }

    subscriptions_in_database = await get_subscriptions_from_database()
    assert subscriptions_in_database == [subscription]


async def test_update_subscription_with_nonexistent_user_fails(
    client: AsyncClient,
    add_products_to_database: AddProductsToDatabase,
    add_subscriptions_to_database: AddSubscriptionsToDatabase,
    add_users_to_database: AddUsersToDatabase,
    get_subscriptions_from_database: GetSubscriptionsFromDatabase,
) -> None:
    product: ProductTuple = (uuid7(), Decimal("9.99"), "Product 1", "published")
    user: UserTuple = (uuid7(), "user@example.com")
    subscription: SubscriptionTuple = (uuid7(), True, user[0], product[0])
    await add_products_to_database(product)
    await add_users_to_database(user)
    await add_subscriptions_to_database(subscription)

    nonexistent_user_id = uuid7()
    response = await client.put(
        f"/subscriptions/{subscription[0]}",
        json={
            "is_active": False,
            "user_id": str(nonexistent_user_id),
            "product_id": str(product[0]),
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"User with ID {nonexistent_user_id} does not exist."
    }

    subscriptions_in_database = await get_subscriptions_from_database()
    assert subscriptions_in_database == [subscription]


async def test_update_subscription_with_nonexistent_product_fails(
    client: AsyncClient,
    add_products_to_database: AddProductsToDatabase,
    add_subscriptions_to_database: AddSubscriptionsToDatabase,
    add_users_to_database: AddUsersToDatabase,
    get_subscriptions_from_database: GetSubscriptionsFromDatabase,
) -> None:
    product: ProductTuple = (uuid7(), Decimal("9.99"), "Product 1", "published")
    user: UserTuple = (uuid7(), "user@example.com")
    subscription: SubscriptionTuple = (uuid7(), True, user[0], product[0])
    await add_products_to_database(product)
    await add_users_to_database(user)
    await add_subscriptions_to_database(subscription)

    nonexistent_product_id = uuid7()
    response = await client.put(
        f"/subscriptions/{subscription[0]}",
        json={
            "is_active": False,
            "user_id": str(user[0]),
            "product_id": str(nonexistent_product_id),
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"Product with ID {nonexistent_product_id} does not exist."
    }

    subscriptions_in_database = await get_subscriptions_from_database()
    assert subscriptions_in_database == [subscription]
