from decimal import Decimal
from typing import TYPE_CHECKING, Literal
from uuid import UUID, uuid4

import pytest
from fastapi import status
from sqlalchemy import Row, select

from app.data_structures.models import ProductModel, SubscriptionModel, UserModel

if TYPE_CHECKING:
    from collections.abc import Sequence

    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


async def _get_subscriptions_from_database(
    session: AsyncSession,
) -> Sequence[Row[tuple[UUID, bool, UUID, UUID]]]:
    statement = select(
        SubscriptionModel.id,
        SubscriptionModel.is_active,
        SubscriptionModel.product_id,
        SubscriptionModel.user_id,
    )
    result = await session.execute(statement)
    return result.all()


async def test_create_subscription_adds_subscription_to_database(
    client: AsyncClient, session: AsyncSession
) -> None:
    product_id = uuid4()
    product_name = "Product 1"
    product_status: Literal["published"] = "published"
    user1_id = uuid4()
    user1_email = "user1@example.com"
    user2_id = uuid4()
    user2_email = "user2@example.com"
    subscription1_id = uuid4()
    subscription1_is_active = True
    async with session.begin():
        session.add_all(
            [
                ProductModel(
                    id=product_id,
                    monthly_fee_in_euros=Decimal("9.99"),
                    name=product_name,
                    status=product_status,
                ),
                UserModel(id=user1_id, email=user1_email),
                UserModel(id=user2_id, email=user2_email),
                SubscriptionModel(
                    id=subscription1_id,
                    is_active=subscription1_is_active,
                    product_id=product_id,
                    user_id=user1_id,
                ),
            ]
        )
        await session.flush()

    new_subscription_id = uuid4()
    new_subscription_is_active = True
    response = await client.post(
        "/subscriptions/",
        json={
            "id": str(new_subscription_id),
            "is_active": new_subscription_is_active,
            "user_id": str(user2_id),
            "product_id": str(product_id),
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() is None

    async with session.begin():
        subscriptions_in_database = await _get_subscriptions_from_database(session)
    assert subscriptions_in_database == [
        (subscription1_id, subscription1_is_active, product_id, user1_id),
        (new_subscription_id, new_subscription_is_active, product_id, user2_id),
    ]


@pytest.mark.parametrize("product_status", ["draft", "deprecated"])
async def test_create_subscription_for_non_published_product_fails(
    client: AsyncClient,
    session: AsyncSession,
    product_status: Literal["draft", "deprecated"],
) -> None:
    product_id = uuid4()
    product_name = "Product 1"
    user_id = uuid4()
    user_email = "user@example.com"
    subscription_id = uuid4()
    async with session.begin():
        session.add_all(
            [
                ProductModel(
                    id=product_id,
                    monthly_fee_in_euros=Decimal("9.99"),
                    name=product_name,
                    status=product_status,
                ),
                UserModel(id=user_id, email=user_email),
            ]
        )
        await session.flush()

    response = await client.post(
        "/subscriptions/",
        json={
            "id": str(subscription_id),
            "is_active": True,
            "user_id": str(user_id),
            "product_id": str(product_id),
        },
    )
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {
        "detail": f"Product with ID {product_id} is in {product_status} status."
    }

    async with session.begin():
        subscriptions_in_database = await _get_subscriptions_from_database(session)
    assert subscriptions_in_database == []


async def test_create_subscription_with_existing_id_fails(
    client: AsyncClient, session: AsyncSession
) -> None:
    product_id = uuid4()
    product_name = "Product 1"
    product_status: Literal["published"] = "published"
    user1_id = uuid4()
    user1_email = "user1@example.com"
    user2_id = uuid4()
    user2_email = "user2@example.com"
    subscription_id = uuid4()
    async with session.begin():
        session.add_all(
            [
                ProductModel(
                    id=product_id,
                    monthly_fee_in_euros=Decimal("9.99"),
                    name=product_name,
                    status=product_status,
                ),
                UserModel(id=user1_id, email=user1_email),
                UserModel(id=user2_id, email=user2_email),
                SubscriptionModel(
                    id=subscription_id,
                    is_active=True,
                    product_id=product_id,
                    user_id=user1_id,
                ),
            ]
        )
        await session.flush()

    response = await client.post(
        "/subscriptions/",
        json={
            "id": str(subscription_id),
            "is_active": False,
            "user_id": str(user2_id),
            "product_id": str(product_id),
        },
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {
        "detail": f"Subscription with ID {subscription_id} already exists."
    }

    async with session.begin():
        subscriptions_in_database = await _get_subscriptions_from_database(session)
    assert subscriptions_in_database == [
        (subscription_id, True, product_id, user1_id),
    ]


async def test_create_subscription_with_nonexistent_user_fails(
    client: AsyncClient, session: AsyncSession
) -> None:
    product_id = uuid4()
    product_name = "Product 1"
    product_status: Literal["published"] = "published"
    user_id = uuid4()
    user_email = "user@example.com"
    subscription_id = uuid4()
    async with session.begin():
        session.add_all(
            [
                ProductModel(
                    id=product_id,
                    monthly_fee_in_euros=Decimal("9.99"),
                    name=product_name,
                    status=product_status,
                ),
                UserModel(id=user_id, email=user_email),
            ]
        )
        await session.flush()

    nonexistent_user_id = uuid4()
    response = await client.post(
        "/subscriptions/",
        json={
            "id": str(subscription_id),
            "is_active": True,
            "user_id": str(nonexistent_user_id),
            "product_id": str(product_id),
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"User with ID {nonexistent_user_id} does not exist."
    }

    async with session.begin():
        subscriptions_in_database = await _get_subscriptions_from_database(session)
    assert subscriptions_in_database == []


async def test_create_subscription_with_nonexistent_product_fails(
    client: AsyncClient, session: AsyncSession
) -> None:
    user_id = uuid4()
    user_email = "user@example.com"
    subscription_id = uuid4()
    async with session.begin():
        session.add(UserModel(id=user_id, email=user_email))
        await session.flush()

    nonexistent_product_id = uuid4()
    response = await client.post(
        "/subscriptions/",
        json={
            "id": str(subscription_id),
            "is_active": True,
            "user_id": str(user_id),
            "product_id": str(nonexistent_product_id),
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"Product with ID {nonexistent_product_id} does not exist."
    }

    async with session.begin():
        subscriptions_in_database = await _get_subscriptions_from_database(session)
    assert subscriptions_in_database == []


async def test_delete_subscription_removes_subscription_from_database(
    client: AsyncClient, session: AsyncSession
) -> None:
    product_id = uuid4()
    product_name = "Product 1"
    product_status: Literal["published"] = "published"
    user1_id = uuid4()
    user1_email = "user1@example.com"
    user2_id = uuid4()
    user2_email = "user2@example.com"
    subscription1_id = uuid4()
    subscription2_id = uuid4()
    async with session.begin():
        session.add_all(
            [
                ProductModel(
                    id=product_id,
                    monthly_fee_in_euros=Decimal("9.99"),
                    name=product_name,
                    status=product_status,
                ),
                UserModel(id=user1_id, email=user1_email),
                UserModel(id=user2_id, email=user2_email),
                SubscriptionModel(
                    id=subscription1_id,
                    is_active=True,
                    product_id=product_id,
                    user_id=user1_id,
                ),
                SubscriptionModel(
                    id=subscription2_id,
                    is_active=False,
                    product_id=product_id,
                    user_id=user2_id,
                ),
            ]
        )
        await session.flush()

    response = await client.delete(f"/subscriptions/{subscription1_id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.content == b""

    async with session.begin():
        subscriptions_in_database = await _get_subscriptions_from_database(session)
    assert subscriptions_in_database == [
        (subscription2_id, False, product_id, user2_id)
    ]


async def test_delete_subscription_with_nonexistent_id_fails(
    client: AsyncClient, session: AsyncSession
) -> None:
    product_id = uuid4()
    product_name = "Product 1"
    product_status: Literal["published"] = "published"
    user_id = uuid4()
    user_email = "user@example.com"
    subscription_id = uuid4()
    async with session.begin():
        session.add_all(
            [
                ProductModel(
                    id=product_id,
                    monthly_fee_in_euros=Decimal("9.99"),
                    name=product_name,
                    status=product_status,
                ),
                UserModel(id=user_id, email=user_email),
                SubscriptionModel(
                    id=subscription_id,
                    is_active=True,
                    product_id=product_id,
                    user_id=user_id,
                ),
            ]
        )
        await session.flush()

    nonexistent_subscription_id = uuid4()
    response = await client.delete(f"/subscriptions/{nonexistent_subscription_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"Subscription with ID {nonexistent_subscription_id} does not exist."
    }

    async with session.begin():
        subscriptions_in_database = await _get_subscriptions_from_database(session)
    assert subscriptions_in_database == [(subscription_id, True, product_id, user_id)]


async def test_read_subscriptions_returns_all_subscriptions(
    client: AsyncClient, session: AsyncSession
) -> None:
    product1_id = uuid4()
    product1_name = "Product 1"
    product1_status: Literal["published"] = "published"
    product2_id = uuid4()
    product2_name = "Product 2"
    product2_status: Literal["published"] = "published"
    user1_id = uuid4()
    user1_email = "user1@example.com"
    user2_id = uuid4()
    user2_email = "user2@example.com"
    subscription1_id = uuid4()
    subscription1_is_active = True
    subscription2_id = uuid4()
    subscription2_is_active = False
    async with session.begin():
        session.add_all(
            [
                ProductModel(
                    id=product1_id,
                    monthly_fee_in_euros=Decimal("9.99"),
                    name=product1_name,
                    status=product1_status,
                ),
                ProductModel(
                    id=product2_id,
                    monthly_fee_in_euros=Decimal("19.99"),
                    name=product2_name,
                    status=product2_status,
                ),
                UserModel(id=user1_id, email=user1_email),
                UserModel(id=user2_id, email=user2_email),
                SubscriptionModel(
                    id=subscription1_id,
                    is_active=subscription1_is_active,
                    product_id=product1_id,
                    user_id=user1_id,
                ),
                SubscriptionModel(
                    id=subscription2_id,
                    is_active=subscription2_is_active,
                    product_id=product2_id,
                    user_id=user2_id,
                ),
            ]
        )
        await session.flush()

    response = await client.get("/subscriptions/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {
            "id": str(subscription1_id),
            "is_active": subscription1_is_active,
            "product": {
                "id": str(product1_id),
                "monthly_fee_in_euros": "9.99",
                "name": product1_name,
                "status": product1_status,
            },
        },
        {
            "id": str(subscription2_id),
            "is_active": subscription2_is_active,
            "product": {
                "id": str(product2_id),
                "monthly_fee_in_euros": "19.99",
                "name": product2_name,
                "status": product2_status,
            },
        },
    ]


async def test_read_subscriptions_returns_empty_list_when_no_subscriptions(
    client: AsyncClient,
) -> None:
    response = await client.get("/subscriptions/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


async def test_read_subscription_by_id_returns_subscription(
    client: AsyncClient, session: AsyncSession
) -> None:
    product_id = uuid4()
    product_name = "Product 1"
    product_status: Literal["published"] = "published"
    user_id = uuid4()
    user_email = "user@example.com"
    subscription_id = uuid4()
    subscription_is_active = True
    async with session.begin():
        session.add_all(
            [
                ProductModel(
                    id=product_id,
                    monthly_fee_in_euros=Decimal("9.99"),
                    name=product_name,
                    status=product_status,
                ),
                UserModel(id=user_id, email=user_email),
                SubscriptionModel(
                    id=subscription_id,
                    is_active=subscription_is_active,
                    product_id=product_id,
                    user_id=user_id,
                ),
            ]
        )
        await session.flush()

    response = await client.get(f"/subscriptions/{subscription_id}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "id": str(subscription_id),
        "is_active": subscription_is_active,
        "product": {
            "id": str(product_id),
            "monthly_fee_in_euros": "9.99",
            "name": product_name,
            "status": product_status,
        },
    }


async def test_read_subscription_by_id_returns_404_when_subscription_does_not_exist(
    client: AsyncClient,
) -> None:
    subscription_id = uuid4()

    response = await client.get(f"/subscriptions/{subscription_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"Subscription with ID {subscription_id} does not exist"
    }


async def test_update_subscription_updates_subscription_in_database(
    client: AsyncClient, session: AsyncSession
) -> None:
    product1_id = uuid4()
    product1_name = "Product 1"
    product1_status: Literal["published"] = "published"
    product2_id = uuid4()
    product2_name = "Product 2"
    product2_status: Literal["published"] = "published"
    user1_id = uuid4()
    user1_email = "user1@example.com"
    user2_id = uuid4()
    user2_email = "user2@example.com"
    subscription_id = uuid4()
    async with session.begin():
        session.add_all(
            [
                ProductModel(
                    id=product1_id,
                    monthly_fee_in_euros=Decimal("9.99"),
                    name=product1_name,
                    status=product1_status,
                ),
                ProductModel(
                    id=product2_id,
                    monthly_fee_in_euros=Decimal("19.99"),
                    name=product2_name,
                    status=product2_status,
                ),
                UserModel(id=user1_id, email=user1_email),
                UserModel(id=user2_id, email=user2_email),
                SubscriptionModel(
                    id=subscription_id,
                    is_active=True,
                    product_id=product1_id,
                    user_id=user1_id,
                ),
            ]
        )
        await session.flush()

    response = await client.put(
        f"/subscriptions/{subscription_id}",
        json={
            "is_active": False,
            "user_id": str(user2_id),
            "product_id": str(product2_id),
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "id": str(subscription_id),
        "is_active": False,
        "product": {
            "id": str(product2_id),
            "monthly_fee_in_euros": "19.99",
            "name": product2_name,
            "status": product2_status,
        },
    }

    async with session.begin():
        subscriptions_in_database = await _get_subscriptions_from_database(session)
    assert subscriptions_in_database == [
        (subscription_id, False, product2_id, user2_id),
    ]


@pytest.mark.parametrize("product_status", ["draft", "deprecated"])
async def test_update_subscription_to_non_published_product_fails(
    client: AsyncClient,
    session: AsyncSession,
    product_status: Literal["draft", "deprecated"],
) -> None:
    published_product_id = uuid4()
    published_product_name = "Published Product"
    non_published_product_id = uuid4()
    non_published_product_name = "Non-Published Product"
    user_id = uuid4()
    user_email = "user@example.com"
    subscription_id = uuid4()
    async with session.begin():
        session.add_all(
            [
                ProductModel(
                    id=published_product_id,
                    monthly_fee_in_euros=Decimal("9.99"),
                    name=published_product_name,
                    status="published",
                ),
                ProductModel(
                    id=non_published_product_id,
                    monthly_fee_in_euros=Decimal("19.99"),
                    name=non_published_product_name,
                    status=product_status,
                ),
                UserModel(id=user_id, email=user_email),
                SubscriptionModel(
                    id=subscription_id,
                    is_active=True,
                    product_id=published_product_id,
                    user_id=user_id,
                ),
            ]
        )
        await session.flush()

    response = await client.put(
        f"/subscriptions/{subscription_id}",
        json={
            "is_active": False,
            "user_id": str(user_id),
            "product_id": str(non_published_product_id),
        },
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {
        "detail": (
            f"Product with ID {non_published_product_id} is in {product_status} status."
        )
    }

    async with session.begin():
        subscriptions_in_database = await _get_subscriptions_from_database(session)
    assert subscriptions_in_database == [
        (subscription_id, True, published_product_id, user_id),
    ]


async def test_update_subscription_with_nonexistent_id_fails(
    client: AsyncClient, session: AsyncSession
) -> None:
    product_id = uuid4()
    product_name = "Product 1"
    product_status: Literal["published"] = "published"
    user_id = uuid4()
    user_email = "user@example.com"
    subscription_id = uuid4()
    async with session.begin():
        session.add_all(
            [
                ProductModel(
                    id=product_id,
                    monthly_fee_in_euros=Decimal("9.99"),
                    name=product_name,
                    status=product_status,
                ),
                UserModel(id=user_id, email=user_email),
                SubscriptionModel(
                    id=subscription_id,
                    is_active=True,
                    product_id=product_id,
                    user_id=user_id,
                ),
            ]
        )
        await session.flush()

    nonexistent_subscription_id = uuid4()
    response = await client.put(
        f"/subscriptions/{nonexistent_subscription_id}",
        json={
            "is_active": False,
            "user_id": str(user_id),
            "product_id": str(product_id),
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"Subscription with ID {nonexistent_subscription_id} does not exist."
    }

    async with session.begin():
        subscriptions_in_database = await _get_subscriptions_from_database(session)
    assert subscriptions_in_database == [
        (subscription_id, True, product_id, user_id),
    ]


async def test_update_subscription_with_nonexistent_user_fails(
    client: AsyncClient, session: AsyncSession
) -> None:
    product_id = uuid4()
    product_name = "Product 1"
    product_status: Literal["published"] = "published"
    user_id = uuid4()
    user_email = "user@example.com"
    subscription_id = uuid4()
    async with session.begin():
        session.add_all(
            [
                ProductModel(
                    id=product_id,
                    monthly_fee_in_euros=Decimal("9.99"),
                    name=product_name,
                    status=product_status,
                ),
                UserModel(id=user_id, email=user_email),
                SubscriptionModel(
                    id=subscription_id,
                    is_active=True,
                    product_id=product_id,
                    user_id=user_id,
                ),
            ]
        )
        await session.flush()

    nonexistent_user_id = uuid4()
    response = await client.put(
        f"/subscriptions/{subscription_id}",
        json={
            "is_active": False,
            "user_id": str(nonexistent_user_id),
            "product_id": str(product_id),
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"User with ID {nonexistent_user_id} does not exist."
    }

    async with session.begin():
        subscriptions_in_database = await _get_subscriptions_from_database(session)
    assert subscriptions_in_database == [
        (subscription_id, True, product_id, user_id),
    ]


async def test_update_subscription_with_nonexistent_product_fails(
    client: AsyncClient, session: AsyncSession
) -> None:
    product_id = uuid4()
    product_name = "Product 1"
    product_status: Literal["published"] = "published"
    user_id = uuid4()
    user_email = "user@example.com"
    subscription_id = uuid4()
    async with session.begin():
        session.add_all(
            [
                ProductModel(
                    id=product_id,
                    monthly_fee_in_euros=Decimal("9.99"),
                    name=product_name,
                    status=product_status,
                ),
                UserModel(id=user_id, email=user_email),
                SubscriptionModel(
                    id=subscription_id,
                    is_active=True,
                    product_id=product_id,
                    user_id=user_id,
                ),
            ]
        )
        await session.flush()

    nonexistent_product_id = uuid4()
    response = await client.put(
        f"/subscriptions/{subscription_id}",
        json={
            "is_active": False,
            "user_id": str(user_id),
            "product_id": str(nonexistent_product_id),
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"Product with ID {nonexistent_product_id} does not exist."
    }

    async with session.begin():
        subscriptions_in_database = await _get_subscriptions_from_database(session)
    assert subscriptions_in_database == [
        (subscription_id, True, product_id, user_id),
    ]
