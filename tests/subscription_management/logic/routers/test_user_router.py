from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import uuid7

from fastapi import status

from subscription_management.data_structures.domain.product import Product
from subscription_management.data_structures.domain.subscription import (
    SubscriptionWithProduct,
    SubscriptionWithUserIdAndProductId,
)
from subscription_management.data_structures.domain.user import (
    User,
    UserWithSubscriptionsWithProducts,
)
from subscription_management.logic.repositories.product_repository import (
    ProductRepository,
)
from subscription_management.logic.repositories.subscription_repository import (
    SubscriptionRepository,
)
from subscription_management.logic.repositories.user_repository import UserRepository

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


async def _select_products(session: AsyncSession) -> tuple[Product, ...]:
    async with session.begin():
        product_repository = ProductRepository(_session=session)
        return await product_repository.read_products()


async def _select_subscriptions(
    session: AsyncSession,
) -> tuple[SubscriptionWithProduct, ...]:
    async with session.begin():
        subscription_repository = _get_subscription_repository(session)
        return await subscription_repository.read_subscriptions()


async def _select_users(
    session: AsyncSession,
) -> tuple[UserWithSubscriptionsWithProducts, ...]:
    async with session.begin():
        user_repository = UserRepository(_session=session)
        return await user_repository.read_users()


def _sorted_by_id(json_objects: Iterable[_JsonObject]) -> list[_JsonObject]:
    return sorted(json_objects, key=_get_id)


def _to_product_json_without_id(product: Product) -> _JsonObject:
    return {
        "monthly_fee_in_euros": str(product.monthly_fee_in_euros),
        "name": product.name,
        "status": product.status,
    }


def _to_product_json(product: Product) -> _JsonObject:
    return {"id": str(product.id)} | _to_product_json_without_id(product)


def _to_subscription_with_product_json(
    subscription: SubscriptionWithProduct,
) -> _JsonObject:
    return {
        "id": str(subscription.id),
        "is_active": subscription.is_active,
        "product": _to_product_json(subscription.product),
    }


def _to_user_json(user: User) -> _JsonObject:
    return {"id": str(user.id), "email": user.email}


def _to_user_with_subscriptions_with_products_json(
    user: UserWithSubscriptionsWithProducts,
) -> _JsonObject:
    return {
        "id": str(user.id),
        "email": user.email,
        "subscriptions": [
            _to_subscription_with_product_json(subscription)
            for subscription in user.subscriptions_with_products
        ],
    }


async def test_create_user_adds_additional_user_to_database(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    users = (
        User(id=uuid7(), email="spam@foo.org"),
        User(id=uuid7(), email="ham@bar.com"),
    )
    await _insert_users(session, *users)

    additional_user = User(id=uuid7(), email="test@baz.com")
    response = await client.post("/users/", json=_to_user_json(additional_user))

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == _to_user_with_subscriptions_with_products_json(
        UserWithSubscriptionsWithProducts(
            id=additional_user.id,
            email=additional_user.email,
            subscriptions_with_products=(),
        )
    )

    users_in_database = await _select_users(session)
    assert frozenset(users_in_database) == frozenset(
        UserWithSubscriptionsWithProducts(
            id=user.id,
            email=user.email,
            subscriptions_with_products=(),
        )
        for user in (*users, additional_user)
    )


async def test_create_user_with_existing_email_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    user = User(id=uuid7(), email="spam@foo.org")
    await _insert_users(session, user)

    response = await client.post(
        "/users/", json={"id": str(uuid7()), "email": user.email}
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {
        "detail": f"User with email {user.email} already exists."
    }

    users_in_database = await _select_users(session)
    assert users_in_database == (
        UserWithSubscriptionsWithProducts(
            id=user.id,
            email=user.email,
            subscriptions_with_products=(),
        ),
    )


async def test_create_user_with_existing_id_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    user = User(id=uuid7(), email="spam@foo.org")
    await _insert_users(session, user)

    response = await client.post(
        "/users/", json={"id": str(user.id), "email": "ham@bar.com"}
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {"detail": f"User with ID {user.id} already exists."}

    users_in_database = await _select_users(session)
    assert users_in_database == (
        UserWithSubscriptionsWithProducts(
            id=user.id,
            email=user.email,
            subscriptions_with_products=(),
        ),
    )


async def test_delete_user_removes_user_from_database(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    users = (
        User(id=uuid7(), email="spam@foo.org"),
        User(id=uuid7(), email="ham@bar.com"),
    )
    await _insert_users(session, *users)

    response = await client.delete(f"/users/{users[0].id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.content == b""

    users_in_database = await _select_users(session)
    assert users_in_database == (
        UserWithSubscriptionsWithProducts(
            id=users[1].id,
            email=users[1].email,
            subscriptions_with_products=(),
        ),
    )


async def test_delete_user_with_nonexistent_id_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    user = User(id=uuid7(), email="spam@foo.org")
    await _insert_users(session, user)

    nonexistent_user_id = uuid7()
    response = await client.delete(f"/users/{nonexistent_user_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"User with ID {nonexistent_user_id} does not exist."
    }

    users_in_database = await _select_users(session)
    assert users_in_database == (
        UserWithSubscriptionsWithProducts(
            id=user.id,
            email=user.email,
            subscriptions_with_products=(),
        ),
    )


async def test_delete_user_also_removes_subscriptions_but_keeps_products(
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
    await _insert_products(session, *products)
    users = (
        User(id=uuid7(), email="user1@example.com"),
        User(id=uuid7(), email="user2@example.com"),
    )
    await _insert_users(session, *users)
    subscriptions = (
        SubscriptionWithUserIdAndProductId(
            id=uuid7(),
            is_active=True,
            user_id=users[0].id,
            product_id=products[0].id,
        ),
        SubscriptionWithUserIdAndProductId(
            id=uuid7(),
            is_active=True,
            user_id=users[1].id,
            product_id=products[1].id,
        ),
    )
    await _insert_subscriptions(session, *subscriptions)

    response = await client.delete(f"/users/{users[0].id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.content == b""

    products_in_database = await _select_products(session)
    assert frozenset(products_in_database) == frozenset(products)
    subscriptions_in_database = await _select_subscriptions(session)
    expected_subscription_with_product = SubscriptionWithProduct(
        id=subscriptions[1].id,
        is_active=subscriptions[1].is_active,
        product=products[1],
    )
    assert subscriptions_in_database == (expected_subscription_with_product,)
    users_in_database = await _select_users(session)
    assert users_in_database == (
        UserWithSubscriptionsWithProducts(
            id=users[1].id,
            email=users[1].email,
            subscriptions_with_products=(expected_subscription_with_product,),
        ),
    )


async def test_read_user_by_email_returns_user(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    product = Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("9.99"),
        name="Test Product",
        status="published",
    )
    await _insert_products(session, product)
    user = User(id=uuid7(), email="test@example.com")
    await _insert_users(session, user)
    subscription = SubscriptionWithUserIdAndProductId(
        id=uuid7(),
        is_active=True,
        user_id=user.id,
        product_id=product.id,
    )
    await _insert_subscriptions(session, subscription)

    response = await client.get(f"/users/by-email/{user.email}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == _to_user_with_subscriptions_with_products_json(
        UserWithSubscriptionsWithProducts(
            id=user.id,
            email=user.email,
            subscriptions_with_products=(
                SubscriptionWithProduct(
                    id=subscription.id,
                    is_active=subscription.is_active,
                    product=product,
                ),
            ),
        )
    )


async def test_read_user_by_email_with_nonexistent_email_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    user = User(id=uuid7(), email="spam@foo.org")
    await _insert_users(session, user)

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
    product = Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("9.99"),
        name="Test Product",
        status="published",
    )
    await _insert_products(session, product)
    user = User(id=uuid7(), email="test@example.com")
    await _insert_users(session, user)
    subscription = SubscriptionWithUserIdAndProductId(
        id=uuid7(),
        is_active=True,
        user_id=user.id,
        product_id=product.id,
    )
    await _insert_subscriptions(session, subscription)

    response = await client.get(f"/users/{user.id}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == _to_user_with_subscriptions_with_products_json(
        UserWithSubscriptionsWithProducts(
            id=user.id,
            email=user.email,
            subscriptions_with_products=(
                SubscriptionWithProduct(
                    id=subscription.id,
                    is_active=subscription.is_active,
                    product=product,
                ),
            ),
        )
    )


async def test_read_user_by_id_with_nonexistent_id_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    user = User(id=uuid7(), email="spam@foo.org")
    await _insert_users(session, user)

    nonexistent_user_id = uuid7()
    response = await client.get(f"/users/{nonexistent_user_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"User with ID {nonexistent_user_id} does not exist."
    }


async def test_read_users_returns_all_users(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    product = Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("9.99"),
        name="Test Product",
        status="published",
    )
    await _insert_products(session, product)
    users = (
        User(id=uuid7(), email="user1@example.com"),
        User(id=uuid7(), email="user2@example.com"),
    )
    await _insert_users(session, *users)
    subscription = SubscriptionWithUserIdAndProductId(
        id=uuid7(),
        is_active=True,
        user_id=users[0].id,
        product_id=product.id,
    )
    await _insert_subscriptions(session, subscription)

    response = await client.get("/users/")

    assert response.status_code == status.HTTP_200_OK
    assert _sorted_by_id(response.json()) == _sorted_by_id(
        (
            _to_user_with_subscriptions_with_products_json(
                UserWithSubscriptionsWithProducts(
                    id=users[0].id,
                    email=users[0].email,
                    subscriptions_with_products=(
                        SubscriptionWithProduct(
                            id=subscription.id,
                            is_active=subscription.is_active,
                            product=product,
                        ),
                    ),
                )
            ),
            _to_user_with_subscriptions_with_products_json(
                UserWithSubscriptionsWithProducts(
                    id=users[1].id,
                    email=users[1].email,
                    subscriptions_with_products=(),
                )
            ),
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
        User(id=uuid7(), email="original@example.com"),
        User(id=uuid7(), email="other@example.com"),
    )
    await _insert_users(session, *users)

    new_email = "updated@example.com"
    response = await client.put(f"/users/{users[0].id}", json={"email": new_email})

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == _to_user_with_subscriptions_with_products_json(
        UserWithSubscriptionsWithProducts(
            id=users[0].id,
            email=new_email,
            subscriptions_with_products=(),
        )
    )

    users_in_database = await _select_users(session)
    assert frozenset(users_in_database) == frozenset(
        (
            UserWithSubscriptionsWithProducts(
                id=users[0].id,
                email=new_email,
                subscriptions_with_products=(),
            ),
            UserWithSubscriptionsWithProducts(
                id=users[1].id,
                email=users[1].email,
                subscriptions_with_products=(),
            ),
        )
    )


async def test_update_user_with_nonexistent_id_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    user = User(id=uuid7(), email="spam@foo.org")
    await _insert_users(session, user)

    nonexistent_user_id = uuid7()
    response = await client.put(
        f"/users/{nonexistent_user_id}", json={"email": "updated@example.com"}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"User with ID {nonexistent_user_id} does not exist."
    }

    users_in_database = await _select_users(session)
    assert users_in_database == (
        UserWithSubscriptionsWithProducts(
            id=user.id,
            email=user.email,
            subscriptions_with_products=(),
        ),
    )


async def test_update_user_with_existing_email_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    users = (
        User(id=uuid7(), email="original@example.com"),
        User(id=uuid7(), email="existing@example.com"),
    )
    await _insert_users(session, *users)

    response = await client.put(f"/users/{users[0].id}", json={"email": users[1].email})

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {
        "detail": f"User with email {users[1].email} already exists."
    }

    users_in_database = await _select_users(session)
    assert frozenset(users_in_database) == frozenset(
        (
            UserWithSubscriptionsWithProducts(
                id=users[0].id,
                email=users[0].email,
                subscriptions_with_products=(),
            ),
            UserWithSubscriptionsWithProducts(
                id=users[1].id,
                email=users[1].email,
                subscriptions_with_products=(),
            ),
        )
    )
