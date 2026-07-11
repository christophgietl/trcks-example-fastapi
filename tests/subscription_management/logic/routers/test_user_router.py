import dataclasses
from collections.abc import Callable, Iterable, Mapping
from decimal import Decimal
from typing import TYPE_CHECKING, Literal, Self, final
from uuid import UUID, uuid7

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


@final
@dataclasses.dataclass(frozen=True, kw_only=True, order=True, slots=True)
class _User:
    id: UUID
    email: str

    async def insert(self, session: AsyncSession) -> None:
        model = UserModel(id=self.id, email=self.email)
        async with session.begin():
            session.add(model)

    @classmethod
    async def select(cls, session: AsyncSession) -> tuple[Self, ...]:
        statement = select(UserModel)
        async with session.begin():
            scalar_result = await session.scalars(statement)
            models = scalar_result.all()
            return tuple(cls(id=model.id, email=model.email) for model in models)

    def to_json(
        self, subscriptions_with_products: Iterable[tuple[_Subscription, _Product]]
    ) -> dict[str, object]:
        return {
            "id": str(self.id),
            "email": self.email,
            "subscriptions": [
                {
                    "id": str(subscription.id),
                    "is_active": subscription.is_active,
                    "product": product.to_json(),
                }
                for subscription, product in subscriptions_with_products
            ],
        }


async def test_create_user_adds_additional_user_to_database(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    users = (
        _User(id=uuid7(), email="spam@foo.org"),
        _User(id=uuid7(), email="ham@bar.com"),
    )
    for user in users:
        await user.insert(session)

    additional_user = _User(id=uuid7(), email="test@baz.com")
    response = await client.post(
        "/users/",
        json={"id": str(additional_user.id), "email": additional_user.email},
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == additional_user.to_json([])

    users_in_database = await _User.select(session)
    assert sorted(users_in_database) == sorted((*users, additional_user))


async def test_create_user_with_existing_email_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    user = _User(id=uuid7(), email="spam@foo.org")
    await user.insert(session)

    response = await client.post(
        "/users/", json={"id": str(uuid7()), "email": user.email}
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {
        "detail": f"User with email {user.email} already exists."
    }

    users_in_database = await _User.select(session)
    assert users_in_database == (user,)


async def test_create_user_with_existing_id_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    user = _User(id=uuid7(), email="spam@foo.org")
    await user.insert(session)

    response = await client.post(
        "/users/", json={"id": str(user.id), "email": "ham@bar.com"}
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {"detail": f"User with ID {user.id} already exists."}

    users_in_database = await _User.select(session)
    assert users_in_database == (user,)


async def test_delete_user_removes_user_from_database(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    users = (
        _User(id=uuid7(), email="spam@foo.org"),
        _User(id=uuid7(), email="ham@bar.com"),
    )
    for user in users:
        await user.insert(session)

    response = await client.delete(f"/users/{users[0].id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.content == b""

    users_in_database = await _User.select(session)
    assert users_in_database == (users[1],)


async def test_delete_user_with_nonexistent_id_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    user = _User(id=uuid7(), email="spam@foo.org")
    await user.insert(session)

    nonexistent_user_id = uuid7()
    response = await client.delete(f"/users/{nonexistent_user_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"User with ID {nonexistent_user_id} does not exist."
    }

    users_in_database = await _User.select(session)
    assert users_in_database == (user,)


async def test_delete_user_also_removes_subscriptions_but_keeps_products(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    products = (
        _Product(
            id=uuid7(),
            monthly_fee_in_euros=Decimal("9.99"),
            name="Product 1",
            status="published",
        ),
        _Product(
            id=uuid7(),
            monthly_fee_in_euros=Decimal("19.99"),
            name="Product 2",
            status="published",
        ),
    )
    users = (
        _User(id=uuid7(), email="user1@example.com"),
        _User(id=uuid7(), email="user2@example.com"),
    )
    subscriptions = (
        _Subscription(
            id=uuid7(),
            is_active=True,
            user_id=users[0].id,
            product_id=products[0].id,
        ),
        _Subscription(
            id=uuid7(),
            is_active=True,
            user_id=users[1].id,
            product_id=products[1].id,
        ),
    )
    for product in products:
        await product.insert(session)
    for user in users:
        await user.insert(session)
    for subscription in subscriptions:
        await subscription.insert(session)

    response = await client.delete(f"/users/{users[0].id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.content == b""

    products_in_database = await _Product.select(session)
    assert {product.id for product in products_in_database} == {
        product.id for product in products
    }
    subscriptions_in_database = await _Subscription.select(session)
    assert subscriptions_in_database == (subscriptions[1],)
    users_in_database = await _User.select(session)
    assert users_in_database == (users[1],)


async def test_read_user_by_email_returns_user(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    product = _Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("9.99"),
        name="Test Product",
        status="published",
    )
    user = _User(id=uuid7(), email="test@example.com")
    subscription = _Subscription(
        id=uuid7(),
        is_active=True,
        user_id=user.id,
        product_id=product.id,
    )
    await product.insert(session)
    await user.insert(session)
    await subscription.insert(session)

    response = await client.get(f"/users/by-email/{user.email}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == user.to_json([(subscription, product)])


async def test_read_user_by_email_with_nonexistent_email_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    user = _User(id=uuid7(), email="spam@foo.org")
    await user.insert(session)

    nonexistent_email = "nonexistent@example.com"
    response = await client.get(f"/users/by-email/{nonexistent_email}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"User with email {nonexistent_email} does not exist."
    }


async def test_read_user_by_id_returns_user(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    product = _Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("9.99"),
        name="Test Product",
        status="published",
    )
    user = _User(id=uuid7(), email="test@example.com")
    subscription = _Subscription(
        id=uuid7(),
        is_active=True,
        user_id=user.id,
        product_id=product.id,
    )
    await product.insert(session)
    await user.insert(session)
    await subscription.insert(session)

    response = await client.get(f"/users/{user.id}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == user.to_json([(subscription, product)])


async def test_read_user_by_id_with_nonexistent_id_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    user = _User(id=uuid7(), email="spam@foo.org")
    await user.insert(session)

    nonexistent_user_id = uuid7()
    response = await client.get(f"/users/{nonexistent_user_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"User with ID {nonexistent_user_id} does not exist."
    }


async def test_read_users_returns_all_users(
    client: AsyncClient,
    session: AsyncSession,
    sorted_by_id: SortedById,
) -> None:
    product = _Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("9.99"),
        name="Test Product",
        status="published",
    )
    users = (
        _User(id=uuid7(), email="user1@example.com"),
        _User(id=uuid7(), email="user2@example.com"),
    )
    subscription = _Subscription(
        id=uuid7(),
        is_active=True,
        user_id=users[0].id,
        product_id=product.id,
    )
    await product.insert(session)
    for user in users:
        await user.insert(session)
    await subscription.insert(session)

    response = await client.get("/users/")

    assert response.status_code == status.HTTP_200_OK
    assert sorted_by_id(response.json()) == sorted_by_id(
        (
            users[0].to_json([(subscription, product)]),
            users[1].to_json([]),
        )
    )


async def test_read_users_returns_empty_list_when_no_users(
    client: AsyncClient,
) -> None:
    response = await client.get("/users/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


async def test_update_user_modifies_user_in_database(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    users = (
        _User(id=uuid7(), email="original@example.com"),
        _User(id=uuid7(), email="other@example.com"),
    )
    for user in users:
        await user.insert(session)

    new_email = "updated@example.com"
    response = await client.put(f"/users/{users[0].id}", json={"email": new_email})

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == _User(id=users[0].id, email=new_email).to_json([])

    users_in_database = await _User.select(session)
    assert sorted(users_in_database) == sorted(
        (_User(id=users[0].id, email=new_email), users[1])
    )


async def test_update_user_with_nonexistent_id_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    user = _User(id=uuid7(), email="spam@foo.org")
    await user.insert(session)

    nonexistent_user_id = uuid7()
    response = await client.put(
        f"/users/{nonexistent_user_id}", json={"email": "updated@example.com"}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"User with ID {nonexistent_user_id} does not exist."
    }

    users_in_database = await _User.select(session)
    assert users_in_database == (user,)


async def test_update_user_with_existing_email_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    users = (
        _User(id=uuid7(), email="original@example.com"),
        _User(id=uuid7(), email="existing@example.com"),
    )
    for user in users:
        await user.insert(session)

    response = await client.put(f"/users/{users[0].id}", json={"email": users[1].email})

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {
        "detail": f"User with email {users[1].email} already exists."
    }

    users_in_database = await _User.select(session)
    assert sorted(users_in_database) == sorted(users)
