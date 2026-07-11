import dataclasses
from collections.abc import Callable, Iterable, Mapping
from decimal import Decimal
from typing import TYPE_CHECKING, Literal, Self, final
from uuid import UUID, uuid7

import pytest
from fastapi import status
from sqlalchemy import select

from subscription_management.data_structures.models import (
    ProductModel,
    SubscriptionModel,
    UserModel,
)

if TYPE_CHECKING:
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession

type _ProductStatus = Literal["draft", "published", "deprecated"]

type SortedById = Callable[[Iterable[StrMapping]], list[StrMapping]]
type StrMapping = Mapping[str, object]


@final
@dataclasses.dataclass(frozen=True, kw_only=True, order=True, slots=True)
class _Product:
    id: UUID
    monthly_fee_in_euros: Decimal
    name: str
    status: _ProductStatus

    async def insert(self, session: AsyncSession) -> None:
        model = ProductModel(
            id=self.id,
            monthly_fee_in_euros=self.monthly_fee_in_euros,
            name=self.name,
            status=self.status,
        )
        async with session.begin():
            session.add(model)

    @classmethod
    async def select(cls, session: AsyncSession) -> tuple[Self, ...]:
        statement = select(ProductModel)
        async with session.begin():
            scalar_result = await session.scalars(statement)
            models = scalar_result.all()
            return tuple(
                cls(
                    id=model.id,
                    monthly_fee_in_euros=model.monthly_fee_in_euros,
                    name=model.name,
                    status=model.status,
                )
                for model in models
            )

    def to_json_without_id(self) -> dict[str, object]:
        return {
            "monthly_fee_in_euros": str(self.monthly_fee_in_euros),
            "name": self.name,
            "status": self.status,
        }

    def to_json(self) -> dict[str, object]:
        return {"id": str(self.id)} | self.to_json_without_id()


@final
@dataclasses.dataclass(frozen=True, kw_only=True, order=True, slots=True)
class _Subscription:
    id: UUID
    is_active: bool
    user_id: UUID
    product_id: UUID

    async def insert(self, session: AsyncSession) -> None:
        model = SubscriptionModel(
            id=self.id,
            is_active=self.is_active,
            user_id=self.user_id,
            product_id=self.product_id,
        )
        async with session.begin():
            session.add(model)

    @classmethod
    async def select(cls, session: AsyncSession) -> tuple[Self, ...]:
        statement = select(SubscriptionModel)
        async with session.begin():
            scalar_result = await session.scalars(statement)
            models = scalar_result.all()
            return tuple(
                cls(
                    id=model.id,
                    is_active=model.is_active,
                    user_id=model.user_id,
                    product_id=model.product_id,
                )
                for model in models
            )

    def to_json(self, product: _Product) -> dict[str, object]:
        return {
            "id": str(self.id),
            "is_active": self.is_active,
            "product": product.to_json(),
        }


@final
@dataclasses.dataclass(frozen=True, kw_only=True, order=True, slots=True)
class _User:
    id: UUID
    email: str

    async def insert(self, session: AsyncSession) -> None:
        model = UserModel(id=self.id, email=self.email)
        async with session.begin():
            session.add(model)


async def test_create_subscription_adds_subscription_to_database(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    product = _Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("9.99"),
        name="Product 1",
        status="published",
    )
    user1 = _User(id=uuid7(), email="user1@example.com")
    user2 = _User(id=uuid7(), email="user2@example.com")
    subscription1 = _Subscription(
        id=uuid7(),
        is_active=True,
        user_id=user1.id,
        product_id=product.id,
    )
    await product.insert(session)
    await user1.insert(session)
    await user2.insert(session)
    await subscription1.insert(session)

    new_subscription = _Subscription(
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
    assert response.json() == new_subscription.to_json(product)

    subscriptions_in_database = await _Subscription.select(session)
    assert sorted(subscriptions_in_database) == sorted(
        (subscription1, new_subscription)
    )


@pytest.mark.parametrize("product_status", ["draft", "deprecated"])
async def test_create_subscription_for_non_published_product_fails(
    client: AsyncClient,
    session: AsyncSession,
    product_status: _ProductStatus,
) -> None:
    product = _Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("9.99"),
        name="Product 1",
        status=product_status,
    )
    user = _User(id=uuid7(), email="user@example.com")
    await product.insert(session)
    await user.insert(session)

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

    subscriptions_in_database = await _Subscription.select(session)
    assert subscriptions_in_database == ()


async def test_create_subscription_with_existing_id_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    product = _Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("9.99"),
        name="Product 1",
        status="published",
    )
    user1 = _User(id=uuid7(), email="user1@example.com")
    user2 = _User(id=uuid7(), email="user2@example.com")
    subscription = _Subscription(
        id=uuid7(),
        is_active=True,
        user_id=user1.id,
        product_id=product.id,
    )
    await product.insert(session)
    await user1.insert(session)
    await user2.insert(session)
    await subscription.insert(session)

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

    subscriptions_in_database = await _Subscription.select(session)
    assert subscriptions_in_database == (subscription,)


async def test_create_subscription_with_nonexistent_user_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    product = _Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("9.99"),
        name="Product 1",
        status="published",
    )
    user = _User(id=uuid7(), email="user@example.com")
    await product.insert(session)
    await user.insert(session)

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

    subscriptions_in_database = await _Subscription.select(session)
    assert subscriptions_in_database == ()


async def test_create_subscription_with_nonexistent_product_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    user = _User(id=uuid7(), email="user@example.com")
    await user.insert(session)

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

    subscriptions_in_database = await _Subscription.select(session)
    assert subscriptions_in_database == ()


async def test_delete_subscription_removes_subscription_from_database(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    product = _Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("9.99"),
        name="Product 1",
        status="published",
    )
    user1 = _User(id=uuid7(), email="user1@example.com")
    user2 = _User(id=uuid7(), email="user2@example.com")
    subscription1 = _Subscription(
        id=uuid7(),
        is_active=True,
        user_id=user1.id,
        product_id=product.id,
    )
    subscription2 = _Subscription(
        id=uuid7(),
        is_active=False,
        user_id=user2.id,
        product_id=product.id,
    )
    await product.insert(session)
    await user1.insert(session)
    await user2.insert(session)
    await subscription1.insert(session)
    await subscription2.insert(session)

    response = await client.delete(f"/subscriptions/{subscription1.id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.content == b""

    subscriptions_in_database = await _Subscription.select(session)
    assert subscriptions_in_database == (subscription2,)


async def test_delete_subscription_with_nonexistent_id_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    product = _Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("9.99"),
        name="Product 1",
        status="published",
    )
    user = _User(id=uuid7(), email="user@example.com")
    subscription = _Subscription(
        id=uuid7(),
        is_active=True,
        user_id=user.id,
        product_id=product.id,
    )
    await product.insert(session)
    await user.insert(session)
    await subscription.insert(session)

    nonexistent_subscription_id = uuid7()
    response = await client.delete(f"/subscriptions/{nonexistent_subscription_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"Subscription with ID {nonexistent_subscription_id} does not exist."
    }

    subscriptions_in_database = await _Subscription.select(session)
    assert subscriptions_in_database == (subscription,)


async def test_read_subscriptions_returns_all_subscriptions(
    client: AsyncClient,
    session: AsyncSession,
    sorted_by_id: SortedById,
) -> None:
    product1 = _Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("9.99"),
        name="Product 1",
        status="published",
    )
    product2 = _Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("19.99"),
        name="Product 2",
        status="published",
    )
    user1 = _User(id=uuid7(), email="user1@example.com")
    user2 = _User(id=uuid7(), email="user2@example.com")
    subscription1 = _Subscription(
        id=uuid7(),
        is_active=True,
        user_id=user1.id,
        product_id=product1.id,
    )
    subscription2 = _Subscription(
        id=uuid7(),
        is_active=False,
        user_id=user2.id,
        product_id=product2.id,
    )
    await product1.insert(session)
    await product2.insert(session)
    await user1.insert(session)
    await user2.insert(session)
    await subscription1.insert(session)
    await subscription2.insert(session)

    response = await client.get("/subscriptions/")

    assert response.status_code == status.HTTP_200_OK
    assert sorted_by_id(response.json()) == sorted_by_id(
        (
            subscription1.to_json(product1),
            subscription2.to_json(product2),
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
    product = _Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("9.99"),
        name="Product 1",
        status="published",
    )
    user = _User(id=uuid7(), email="user@example.com")
    subscription = _Subscription(
        id=uuid7(),
        is_active=True,
        user_id=user.id,
        product_id=product.id,
    )
    await product.insert(session)
    await user.insert(session)
    await subscription.insert(session)

    response = await client.get(f"/subscriptions/{subscription.id}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == subscription.to_json(product)


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
    product1 = _Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("9.99"),
        name="Product 1",
        status="published",
    )
    product2 = _Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("19.99"),
        name="Product 2",
        status="published",
    )
    user1 = _User(id=uuid7(), email="user1@example.com")
    user2 = _User(id=uuid7(), email="user2@example.com")
    subscription = _Subscription(
        id=uuid7(),
        is_active=True,
        user_id=user1.id,
        product_id=product1.id,
    )
    await product1.insert(session)
    await product2.insert(session)
    await user1.insert(session)
    await user2.insert(session)
    await subscription.insert(session)

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
    assert response.json() == updated_subscription.to_json(product2)

    subscriptions_in_database = await _Subscription.select(session)
    assert subscriptions_in_database == (updated_subscription,)


@pytest.mark.parametrize("product_status", ["draft", "deprecated"])
async def test_update_subscription_to_non_published_product_fails(
    client: AsyncClient,
    session: AsyncSession,
    product_status: _ProductStatus,
) -> None:
    published_product = _Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("9.99"),
        name="Published Product",
        status="published",
    )
    non_published_product = _Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("19.99"),
        name="Non-Published Product",
        status=product_status,
    )
    user = _User(id=uuid7(), email="user@example.com")
    subscription = _Subscription(
        id=uuid7(),
        is_active=True,
        user_id=user.id,
        product_id=published_product.id,
    )
    await published_product.insert(session)
    await non_published_product.insert(session)
    await user.insert(session)
    await subscription.insert(session)

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

    subscriptions_in_database = await _Subscription.select(session)
    assert subscriptions_in_database == (subscription,)


async def test_update_subscription_with_nonexistent_id_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    product = _Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("9.99"),
        name="Product 1",
        status="published",
    )
    user = _User(id=uuid7(), email="user@example.com")
    subscription = _Subscription(
        id=uuid7(),
        is_active=True,
        user_id=user.id,
        product_id=product.id,
    )
    await product.insert(session)
    await user.insert(session)
    await subscription.insert(session)

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

    subscriptions_in_database = await _Subscription.select(session)
    assert subscriptions_in_database == (subscription,)


async def test_update_subscription_with_nonexistent_user_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    product = _Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("9.99"),
        name="Product 1",
        status="published",
    )
    user = _User(id=uuid7(), email="user@example.com")
    subscription = _Subscription(
        id=uuid7(),
        is_active=True,
        user_id=user.id,
        product_id=product.id,
    )
    await product.insert(session)
    await user.insert(session)
    await subscription.insert(session)

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

    subscriptions_in_database = await _Subscription.select(session)
    assert subscriptions_in_database == (subscription,)


async def test_update_subscription_with_nonexistent_product_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    product = _Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("9.99"),
        name="Product 1",
        status="published",
    )
    user = _User(id=uuid7(), email="user@example.com")
    subscription = _Subscription(
        id=uuid7(),
        is_active=True,
        user_id=user.id,
        product_id=product.id,
    )
    await product.insert(session)
    await user.insert(session)
    await subscription.insert(session)

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

    subscriptions_in_database = await _Subscription.select(session)
    assert subscriptions_in_database == (subscription,)
