from decimal import Decimal
from typing import TYPE_CHECKING, Literal
from uuid import UUID, uuid4

from fastapi import status
from sqlalchemy import Row, select

from app.data_structures.models import ProductModel, SubscriptionModel, UserModel

if TYPE_CHECKING:
    from collections.abc import Sequence

    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


async def _get_users_from_database(
    session: AsyncSession,
) -> Sequence[Row[tuple[UUID, str]]]:
    statement = select(UserModel.id, UserModel.email)
    result = await session.execute(statement)
    return result.all()


async def test_create_user_adds_additional_user_to_database(
    client: AsyncClient, session: AsyncSession
) -> None:
    users = ((uuid4(), "spam@foo.org"), (uuid4(), "ham@bar.com"))
    async with session.begin():
        session.add_all(UserModel(id=user[0], email=user[1]) for user in users)
        await session.flush()

    additional_user = (uuid4(), "test@baz.com")
    response = await client.post(
        "/users/", json={"id": str(additional_user[0]), "email": additional_user[1]}
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() is None

    async with session.begin():
        users_in_database = await _get_users_from_database(session)
    assert users_in_database == [*users, additional_user]


async def test_create_user_with_existing_email_fails(
    client: AsyncClient, session: AsyncSession
) -> None:
    user = (uuid4(), "spam@foo.org")
    async with session.begin():
        session.add(UserModel(id=user[0], email=user[1]))
        await session.flush()

    response = await client.post("/users/", json={"id": str(uuid4()), "email": user[1]})

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {"detail": f"User with email {user[1]} already exists."}

    async with session.begin():
        users_in_database = await _get_users_from_database(session)
    assert users_in_database == [user]


async def test_create_user_with_existing_id_fails(
    client: AsyncClient, session: AsyncSession
) -> None:
    user = (uuid4(), "spam@foo.org")
    async with session.begin():
        session.add(UserModel(id=user[0], email=user[1]))
        await session.flush()

    response = await client.post(
        "/users/", json={"id": str(user[0]), "email": "ham@bar.com"}
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {"detail": f"User with ID {user[0]} already exists."}

    async with session.begin():
        users_in_database = await _get_users_from_database(session)
    assert users_in_database == [user]


async def test_delete_user_removes_user_from_database(
    client: AsyncClient, session: AsyncSession
) -> None:
    users = ((uuid4(), "spam@foo.org"), (uuid4(), "ham@bar.com"))
    async with session.begin():
        session.add_all(UserModel(id=user[0], email=user[1]) for user in users)
        await session.flush()

    response = await client.delete(f"/users/{users[0][0]}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.content == b""

    async with session.begin():
        users_in_database = await _get_users_from_database(session)
    assert users_in_database == [users[1]]


async def test_delete_user_with_nonexistent_id_fails(
    client: AsyncClient, session: AsyncSession
) -> None:
    user = (uuid4(), "spam@foo.org")
    async with session.begin():
        session.add(UserModel(id=user[0], email=user[1]))
        await session.flush()

    nonexistent_user_id = uuid4()
    response = await client.delete(f"/users/{nonexistent_user_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"User with ID {nonexistent_user_id} does not exist."
    }

    async with session.begin():
        users_in_database = await _get_users_from_database(session)
    assert users_in_database == [user]


async def test_read_user_by_email_returns_user(
    client: AsyncClient, session: AsyncSession
) -> None:
    product_id = uuid4()
    product_monthly_fee_in_euros = Decimal("9.99")
    product_name = "Test Product"
    product_status: Literal["published"] = "published"
    user_id = uuid4()
    user_email = "test@example.com"
    subscription_id = uuid4()
    subscription_is_active = True
    async with session.begin():
        session.add(
            ProductModel(
                id=product_id,
                monthly_fee_in_euros=product_monthly_fee_in_euros,
                name=product_name,
                status=product_status,
            )
        )
        session.add(UserModel(id=user_id, email=user_email))
        session.add(
            SubscriptionModel(
                id=subscription_id,
                is_active=subscription_is_active,
                product_id=product_id,
                user_id=user_id,
            )
        )
        await session.flush()

    response = await client.get(f"/users/by-email/{user_email}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "id": str(user_id),
        "email": user_email,
        "subscriptions": [
            {
                "id": str(subscription_id),
                "is_active": subscription_is_active,
                "product": {
                    "id": str(product_id),
                    "monthly_fee_in_euros": str(product_monthly_fee_in_euros),
                    "name": product_name,
                    "status": product_status,
                },
            }
        ],
    }


async def test_read_user_by_email_with_nonexistent_email_fails(
    client: AsyncClient, session: AsyncSession
) -> None:
    user = (uuid4(), "spam@foo.org")
    async with session.begin():
        session.add(UserModel(id=user[0], email=user[1]))
        await session.flush()

    nonexistent_email = "nonexistent@example.com"
    response = await client.get(f"/users/by-email/{nonexistent_email}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"User with email {nonexistent_email} does not exist."
    }


async def test_read_user_by_id_returns_user(
    client: AsyncClient, session: AsyncSession
) -> None:
    product: tuple[UUID, Decimal, str, Literal["published"]] = (
        uuid4(),
        Decimal("9.99"),
        "Test Product",
        "published",
    )
    user = (uuid4(), "test@example.com")
    subscription = (uuid4(), True, product[0], user[0])
    async with session.begin():
        session.add(
            ProductModel(
                id=product[0],
                monthly_fee_in_euros=product[1],
                name=product[2],
                status=product[3],
            )
        )
        session.add(UserModel(id=user[0], email=user[1]))
        session.add(
            SubscriptionModel(
                id=subscription[0],
                is_active=subscription[1],
                product_id=subscription[2],
                user_id=subscription[3],
            )
        )
        await session.flush()

    response = await client.get(f"/users/{user[0]}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "id": str(user[0]),
        "email": user[1],
        "subscriptions": [
            {
                "id": str(subscription[0]),
                "is_active": subscription[1],
                "product": {
                    "id": str(product[0]),
                    "monthly_fee_in_euros": str(product[1]),
                    "name": product[2],
                    "status": product[3],
                },
            }
        ],
    }


async def test_read_user_by_id_with_nonexistent_id_fails(
    client: AsyncClient, session: AsyncSession
) -> None:
    user = (uuid4(), "spam@foo.org")
    async with session.begin():
        session.add(UserModel(id=user[0], email=user[1]))
        await session.flush()

    nonexistent_user_id = uuid4()
    response = await client.get(f"/users/{nonexistent_user_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"User with ID {nonexistent_user_id} does not exist."
    }


async def test_read_users_returns_all_users(
    client: AsyncClient, session: AsyncSession
) -> None:
    product_id = uuid4()
    product_monthly_fee_in_euros = Decimal("9.99")
    product_name = "Test Product"
    product_status: Literal["published"] = "published"
    user1_id = uuid4()
    user1_email = "user1@example.com"
    user2_id = uuid4()
    user2_email = "user2@example.com"
    subscription_id = uuid4()
    subscription_is_active = True
    async with session.begin():
        session.add(
            ProductModel(
                id=product_id,
                monthly_fee_in_euros=product_monthly_fee_in_euros,
                name=product_name,
                status=product_status,
            )
        )
        session.add(UserModel(id=user1_id, email=user1_email))
        session.add(UserModel(id=user2_id, email=user2_email))
        session.add(
            SubscriptionModel(
                id=subscription_id,
                is_active=subscription_is_active,
                product_id=product_id,
                user_id=user1_id,
            )
        )
        await session.flush()

    response = await client.get("/users/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {
            "id": str(user1_id),
            "email": user1_email,
            "subscriptions": [
                {
                    "id": str(subscription_id),
                    "is_active": subscription_is_active,
                    "product": {
                        "id": str(product_id),
                        "monthly_fee_in_euros": str(product_monthly_fee_in_euros),
                        "name": product_name,
                        "status": product_status,
                    },
                }
            ],
        },
        {"id": str(user2_id), "email": user2_email, "subscriptions": []},
    ]


async def test_read_users_returns_empty_list_when_no_users(client: AsyncClient) -> None:
    response = await client.get("/users/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


async def test_update_user_modifies_user_in_database(
    client: AsyncClient, session: AsyncSession
) -> None:
    users = ((uuid4(), "original@example.com"), (uuid4(), "other@example.com"))
    async with session.begin():
        session.add_all(UserModel(id=user[0], email=user[1]) for user in users)
        await session.flush()

    new_email = "updated@example.com"
    response = await client.put(f"/users/{users[0][0]}", json={"email": new_email})

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "id": str(users[0][0]),
        "email": new_email,
        "subscriptions": [],
    }

    async with session.begin():
        users_in_database = await _get_users_from_database(session)
    assert users_in_database == [(users[0][0], new_email), users[1]]


async def test_update_user_with_nonexistent_id_fails(
    client: AsyncClient, session: AsyncSession
) -> None:
    user = (uuid4(), "spam@foo.org")
    async with session.begin():
        session.add(UserModel(id=user[0], email=user[1]))
        await session.flush()

    nonexistent_user_id = uuid4()
    response = await client.put(
        f"/users/{nonexistent_user_id}", json={"email": "updated@example.com"}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"User with ID {nonexistent_user_id} does not exist."
    }

    async with session.begin():
        users_in_database = await _get_users_from_database(session)
    assert users_in_database == [user]


async def test_update_user_with_existing_email_fails(
    client: AsyncClient, session: AsyncSession
) -> None:
    users = ((uuid4(), "original@example.com"), (uuid4(), "existing@example.com"))
    async with session.begin():
        session.add_all(UserModel(id=user[0], email=user[1]) for user in users)
        await session.flush()

    response = await client.put(f"/users/{users[0][0]}", json={"email": users[1][1]})

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {
        "detail": f"User with email {users[1][1]} already exists."
    }

    async with session.begin():
        users_in_database = await _get_users_from_database(session)
    assert users_in_database == [*users]
