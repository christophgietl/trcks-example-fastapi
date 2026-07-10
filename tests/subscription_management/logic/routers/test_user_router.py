from collections.abc import Awaitable, Callable, Iterable, Sequence
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid7

from fastapi import status

from subscription_management.data_structures.domain.product import ProductStatus
from subscription_management.data_structures.models import (
    ProductModel,
    SubscriptionModel,
    UserModel,
)

if TYPE_CHECKING:
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession

type GetProductsFromDatabase = Callable[[], Awaitable[Sequence[ProductTuple]]]
type GetSubscriptionsFromDatabase = Callable[[], Awaitable[Sequence[SubscriptionTuple]]]
type GetUsersFromDatabase = Callable[[], Awaitable[Sequence[UserTuple]]]
type ProductTuple = tuple[UUID, Decimal, str, ProductStatus]
type ProductTuples = tuple[ProductTuple, ...]
type SortedById = Callable[[Iterable[StrDict]], list[StrDict]]
type StrDict = dict[str, object]
type SubscriptionTuple = tuple[UUID, bool, UUID, UUID]
type SubscriptionTuples = tuple[SubscriptionTuple, ...]
type UserTuple = tuple[UUID, str]
type UserTuples = tuple[UserTuple, ...]


def _to_product_dict(product: ProductTuple) -> StrDict:
    return {
        "id": str(product[0]),
        "monthly_fee_in_euros": str(product[1]),
        "name": product[2],
        "status": product[3],
    }


def _to_subscription_dict(
    subscription: SubscriptionTuple, product: ProductTuple
) -> StrDict:
    return {
        "id": str(subscription[0]),
        "is_active": subscription[1],
        "product": _to_product_dict(product),
    }


def _to_user_dict(
    user: UserTuple, subscriptions: Iterable[tuple[SubscriptionTuple, ProductTuple]]
) -> StrDict:
    return {
        "id": str(user[0]),
        "email": user[1],
        "subscriptions": [
            _to_subscription_dict(subscription, product)
            for subscription, product in subscriptions
        ],
    }


async def test_create_user_adds_additional_user_to_database(
    client: AsyncClient,
    get_users_from_database: GetUsersFromDatabase,
    session: AsyncSession,
) -> None:
    users: UserTuples = ((uuid7(), "spam@foo.org"), (uuid7(), "ham@bar.com"))
    user_models = tuple(UserModel(*user) for user in users)
    async with session.begin():
        session.add_all(user_models)

    additional_user: UserTuple = (uuid7(), "test@baz.com")
    response = await client.post(
        "/users/", json={"id": str(additional_user[0]), "email": additional_user[1]}
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == _to_user_dict(additional_user, [])

    users_in_database = await get_users_from_database()
    assert sorted(users_in_database) == sorted((*users, additional_user))


async def test_create_user_with_existing_email_fails(
    client: AsyncClient,
    get_users_from_database: GetUsersFromDatabase,
    session: AsyncSession,
) -> None:
    user: UserTuple = (uuid7(), "spam@foo.org")
    user_model = UserModel(*user)
    async with session.begin():
        session.add(user_model)

    response = await client.post("/users/", json={"id": str(uuid7()), "email": user[1]})

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {"detail": f"User with email {user[1]} already exists."}

    users_in_database = await get_users_from_database()
    assert users_in_database == [user]


async def test_create_user_with_existing_id_fails(
    client: AsyncClient,
    get_users_from_database: GetUsersFromDatabase,
    session: AsyncSession,
) -> None:
    user: UserTuple = (uuid7(), "spam@foo.org")
    user_model = UserModel(*user)
    async with session.begin():
        session.add(user_model)

    response = await client.post(
        "/users/", json={"id": str(user[0]), "email": "ham@bar.com"}
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {"detail": f"User with ID {user[0]} already exists."}

    users_in_database = await get_users_from_database()
    assert users_in_database == [user]


async def test_delete_user_removes_user_from_database(
    client: AsyncClient,
    get_users_from_database: GetUsersFromDatabase,
    session: AsyncSession,
) -> None:
    users: UserTuples = ((uuid7(), "spam@foo.org"), (uuid7(), "ham@bar.com"))
    user_models = tuple(UserModel(*user) for user in users)
    async with session.begin():
        session.add_all(user_models)

    response = await client.delete(f"/users/{users[0][0]}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.content == b""

    users_in_database = await get_users_from_database()
    assert users_in_database == [users[1]]


async def test_delete_user_with_nonexistent_id_fails(
    client: AsyncClient,
    get_users_from_database: GetUsersFromDatabase,
    session: AsyncSession,
) -> None:
    user: UserTuple = (uuid7(), "spam@foo.org")
    user_model = UserModel(*user)
    async with session.begin():
        session.add(user_model)

    nonexistent_user_id = uuid7()
    response = await client.delete(f"/users/{nonexistent_user_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"User with ID {nonexistent_user_id} does not exist."
    }

    users_in_database = await get_users_from_database()
    assert users_in_database == [user]


async def test_delete_user_also_removes_subscriptions_but_keeps_products(
    client: AsyncClient,
    get_products_from_database: GetProductsFromDatabase,
    get_subscriptions_from_database: GetSubscriptionsFromDatabase,
    get_users_from_database: GetUsersFromDatabase,
    session: AsyncSession,
) -> None:
    products: ProductTuples = (
        (uuid7(), Decimal("9.99"), "Product 1", "published"),
        (uuid7(), Decimal("19.99"), "Product 2", "published"),
    )
    users: UserTuples = (
        (uuid7(), "user1@example.com"),
        (uuid7(), "user2@example.com"),
    )
    subscriptions: SubscriptionTuples = (
        (uuid7(), True, users[0][0], products[0][0]),
        (uuid7(), True, users[1][0], products[1][0]),
    )
    models = (
        *(ProductModel(*product) for product in products),
        *(UserModel(*user) for user in users),
        *(SubscriptionModel(*subscription) for subscription in subscriptions),
    )
    async with session.begin():
        session.add_all(models)

    response = await client.delete(f"/users/{users[0][0]}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.content == b""

    products_in_database = await get_products_from_database()
    assert {product[0] for product in products_in_database} == {
        product[0] for product in products
    }
    subscriptions_in_database = await get_subscriptions_from_database()
    assert subscriptions_in_database == [
        (
            subscriptions[1][0],
            subscriptions[1][1],
            subscriptions[1][2],
            subscriptions[1][3],
        )
    ]
    users_in_database = await get_users_from_database()
    assert users_in_database == [users[1]]


async def test_read_user_by_email_returns_user(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    product: ProductTuple = (uuid7(), Decimal("9.99"), "Test Product", "published")
    user: UserTuple = (uuid7(), "test@example.com")
    subscription: SubscriptionTuple = (uuid7(), True, user[0], product[0])
    async with session.begin():
        session.add(ProductModel(*product))
        session.add(UserModel(*user))
        session.add(SubscriptionModel(*subscription))

    response = await client.get(f"/users/by-email/{user[1]}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == _to_user_dict(user, [(subscription, product)])


async def test_read_user_by_email_with_nonexistent_email_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    user: UserTuple = (uuid7(), "spam@foo.org")
    user_model = UserModel(*user)
    async with session.begin():
        session.add(user_model)

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
    product: ProductTuple = (uuid7(), Decimal("9.99"), "Test Product", "published")
    user: UserTuple = (uuid7(), "test@example.com")
    subscription: SubscriptionTuple = (uuid7(), True, user[0], product[0])
    async with session.begin():
        session.add(ProductModel(*product))
        session.add(UserModel(*user))
        session.add(SubscriptionModel(*subscription))

    response = await client.get(f"/users/{user[0]}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == _to_user_dict(user, [(subscription, product)])


async def test_read_user_by_id_with_nonexistent_id_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    user: UserTuple = (uuid7(), "spam@foo.org")
    user_model = UserModel(*user)
    async with session.begin():
        session.add(user_model)

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
    product: ProductTuple = (uuid7(), Decimal("9.99"), "Test Product", "published")
    users: UserTuples = (
        (uuid7(), "user1@example.com"),
        (uuid7(), "user2@example.com"),
    )
    subscription: SubscriptionTuple = (uuid7(), True, users[0][0], product[0])
    user_models = tuple(UserModel(*user) for user in users)
    async with session.begin():
        session.add(ProductModel(*product))
        session.add_all(user_models)
        session.add(SubscriptionModel(*subscription))

    response = await client.get("/users/")

    assert response.status_code == status.HTTP_200_OK
    assert sorted_by_id(response.json()) == sorted_by_id(
        (
            _to_user_dict(users[0], [(subscription, product)]),
            _to_user_dict(users[1], []),
        )
    )


async def test_read_users_returns_empty_list_when_no_users(client: AsyncClient) -> None:
    response = await client.get("/users/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


async def test_update_user_modifies_user_in_database(
    client: AsyncClient,
    get_users_from_database: GetUsersFromDatabase,
    session: AsyncSession,
) -> None:
    users: UserTuples = (
        (uuid7(), "original@example.com"),
        (uuid7(), "other@example.com"),
    )
    user_models = tuple(UserModel(*user) for user in users)
    async with session.begin():
        session.add_all(user_models)

    new_email = "updated@example.com"
    response = await client.put(f"/users/{users[0][0]}", json={"email": new_email})

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == _to_user_dict((users[0][0], new_email), [])

    users_in_database = await get_users_from_database()
    assert sorted(users_in_database) == sorted(((users[0][0], new_email), users[1]))


async def test_update_user_with_nonexistent_id_fails(
    client: AsyncClient,
    get_users_from_database: GetUsersFromDatabase,
    session: AsyncSession,
) -> None:
    user: UserTuple = (uuid7(), "spam@foo.org")
    user_model = UserModel(*user)
    async with session.begin():
        session.add(user_model)

    nonexistent_user_id = uuid7()
    response = await client.put(
        f"/users/{nonexistent_user_id}", json={"email": "updated@example.com"}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"User with ID {nonexistent_user_id} does not exist."
    }

    users_in_database = await get_users_from_database()
    assert users_in_database == [user]


async def test_update_user_with_existing_email_fails(
    client: AsyncClient,
    get_users_from_database: GetUsersFromDatabase,
    session: AsyncSession,
) -> None:
    users: UserTuples = (
        (uuid7(), "original@example.com"),
        (uuid7(), "existing@example.com"),
    )
    user_models = tuple(UserModel(*user) for user in users)
    async with session.begin():
        session.add_all(user_models)

    response = await client.put(f"/users/{users[0][0]}", json={"email": users[1][1]})

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {
        "detail": f"User with email {users[1][1]} already exists."
    }

    users_in_database = await get_users_from_database()
    assert sorted(users_in_database) == sorted(users)
