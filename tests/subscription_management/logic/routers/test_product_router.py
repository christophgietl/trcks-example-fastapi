from collections.abc import Callable, Iterable, Sequence
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid7

import pytest
from fastapi import status
from sqlalchemy import Row, select

from subscription_management.data_structures.domain.product import ProductStatus
from subscription_management.data_structures.models import ProductModel

if TYPE_CHECKING:
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession

type ProductTuple = tuple[UUID, Decimal, str, ProductStatus]
type ProductTuples = tuple[ProductTuple, ...]
type SortedById = Callable[[Iterable[StrDict]], list[StrDict]]
type StrDict = dict[str, object]
type ToProductDict = Callable[[ProductTuple], StrDict]


async def _get_products_from_database(
    session: AsyncSession,
) -> Sequence[Row[ProductTuple]]:
    statement = select(
        ProductModel.id,
        ProductModel.monthly_fee_in_euros,
        ProductModel.name,
        ProductModel.status,
    )
    result = await session.execute(statement)
    return result.all()


async def test_create_product_adds_additional_product_to_database(
    client: AsyncClient, session: AsyncSession, to_product_dict: ToProductDict
) -> None:
    products: ProductTuples = (
        (uuid7(), Decimal("6.99"), "Product 1", "published"),
        (uuid7(), Decimal("3.25"), "Product 2", "published"),
    )
    product_models = tuple(ProductModel(*product) for product in products)
    async with session.begin():
        session.add_all(product_models)

    additional_product: ProductTuple = (
        uuid7(),
        Decimal("9.99"),
        "Product 3",
        "published",
    )
    additional_product_as_dict = to_product_dict(additional_product)
    response = await client.post("/products/", json=additional_product_as_dict)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == additional_product_as_dict

    async with session.begin():
        products_in_database = await _get_products_from_database(session)
    assert sorted(products_in_database) == sorted((*products, additional_product))


async def test_create_product_with_existing_id_fails(
    client: AsyncClient, session: AsyncSession
) -> None:
    product: ProductTuple = (
        uuid7(),
        Decimal("5.99"),
        "Test Product",
        "published",
    )
    product_model = ProductModel(*product)
    async with session.begin():
        session.add(product_model)

    additional_product_with_existing_id_as_dict = {
        "id": str(product[0]),
        "monthly_fee_in_euros": "8.49",
        "name": "Different Product",
        "status": "published",
    }
    response = await client.post(
        "/products/",
        json=additional_product_with_existing_id_as_dict,
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {
        "detail": f"Product with ID {product[0]} already exists."
    }

    async with session.begin():
        products_in_database = await _get_products_from_database(session)
    assert products_in_database == [product]


async def test_create_product_with_existing_name_fails(
    client: AsyncClient, session: AsyncSession
) -> None:
    product: ProductTuple = (uuid7(), Decimal("5.99"), "Test Product", "published")
    product_model = ProductModel(*product)
    async with session.begin():
        session.add(product_model)

    additional_product_with_existing_name_as_dict = {
        "id": str(uuid7()),
        "monthly_fee_in_euros": "8.49",
        "name": product[2],
        "status": "published",
    }
    response = await client.post(
        "/products/", json=additional_product_with_existing_name_as_dict
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {
        "detail": f"Product with name {product[2]} already exists."
    }

    async with session.begin():
        products_in_database = await _get_products_from_database(session)
    assert products_in_database == [product]


async def test_delete_product_removes_draft_product_from_database(
    client: AsyncClient, session: AsyncSession
) -> None:
    products: ProductTuples = (
        (uuid7(), Decimal("0.89"), "Product 1", "draft"),
        (uuid7(), Decimal("0.69"), "Product 2", "published"),
    )
    product_models = tuple(ProductModel(*product) for product in products)
    async with session.begin():
        session.add_all(product_models)

    response = await client.delete(f"/products/{products[0][0]}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.content == b""

    async with session.begin():
        products_in_database = await _get_products_from_database(session)
    assert products_in_database == [products[1]]


async def test_delete_product_with_nonexistent_id_fails(
    client: AsyncClient, session: AsyncSession
) -> None:
    product: ProductTuple = (
        uuid7(),
        Decimal("2.99"),
        "Test Product",
        "published",
    )
    product_model = ProductModel(*product)
    async with session.begin():
        session.add(product_model)

    nonexistent_product_id = uuid7()
    response = await client.delete(f"/products/{nonexistent_product_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"Product with ID {nonexistent_product_id} does not exist."
    }

    async with session.begin():
        products_in_database = await _get_products_from_database(session)
    assert products_in_database == [product]


@pytest.mark.parametrize("product_status", ["published", "deprecated"])
async def test_delete_product_with_non_draft_status_fails(
    client: AsyncClient, session: AsyncSession, product_status: ProductStatus
) -> None:
    product: ProductTuple = (uuid7(), Decimal("3.99"), "Test Product", product_status)
    product_model = ProductModel(*product)
    async with session.begin():
        session.add(product_model)

    response = await client.delete(f"/products/{product[0]}")

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {
        "detail": (
            f"Product with ID {product[0]} cannot be deleted "
            f"because its status is {product_status}."
        )
    }

    async with session.begin():
        products_in_database = await _get_products_from_database(session)
    assert products_in_database == [product]


async def test_read_product_by_id_returns_product(
    client: AsyncClient, session: AsyncSession, to_product_dict: ToProductDict
) -> None:
    product: ProductTuple = (uuid7(), Decimal("1.99"), "Test Product", "published")
    product_model = ProductModel(*product)
    async with session.begin():
        session.add(product_model)

    response = await client.get(f"/products/{product[0]}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == to_product_dict(product)


async def test_read_product_by_id_with_nonexistent_id_fails(
    client: AsyncClient, session: AsyncSession
) -> None:
    product: ProductTuple = (uuid7(), Decimal("1.99"), "Test Product", "published")
    product_model = ProductModel(*product)
    async with session.begin():
        session.add(product_model)

    nonexistent_product_id = uuid7()
    response = await client.get(f"/products/{nonexistent_product_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"Product with ID {nonexistent_product_id} does not exist."
    }


async def test_read_product_by_name_returns_product(
    client: AsyncClient, session: AsyncSession, to_product_dict: ToProductDict
) -> None:
    product: ProductTuple = (uuid7(), Decimal("1.99"), "Test Product", "published")
    product_model = ProductModel(*product)
    async with session.begin():
        session.add(product_model)

    response = await client.get(f"/products/by-name/{product[2]}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == to_product_dict(product)


async def test_read_product_by_name_with_nonexistent_name_fails(
    client: AsyncClient, session: AsyncSession
) -> None:
    product: ProductTuple = (uuid7(), Decimal("1.99"), "Test Product", "published")
    product_model = ProductModel(*product)
    async with session.begin():
        session.add(product_model)

    nonexistent_product_name = "Nonexistent Product"
    response = await client.get(f"/products/by-name/{nonexistent_product_name}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"Product with name {nonexistent_product_name} does not exist."
    }


async def test_read_products_returns_all_products(
    client: AsyncClient,
    session: AsyncSession,
    sorted_by_id: SortedById,
    to_product_dict: ToProductDict,
) -> None:
    products: ProductTuples = (
        (uuid7(), Decimal("4.99"), "Product 1", "published"),
        (uuid7(), Decimal("2.99"), "Product 2", "published"),
    )
    product_models = tuple(ProductModel(*product) for product in products)
    async with session.begin():
        session.add_all(product_models)

    response = await client.get("/products/")

    assert response.status_code == status.HTTP_200_OK
    assert sorted_by_id(response.json()) == sorted_by_id(
        to_product_dict(product) for product in products
    )


async def test_read_products_returns_empty_list_when_no_products(
    client: AsyncClient,
) -> None:
    response = await client.get("/products/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


@pytest.mark.parametrize("product_status", ["published", "deprecated"])
async def test_update_product_cannot_change_non_status_attributes_of_published_product(
    client: AsyncClient, session: AsyncSession, product_status: ProductStatus
) -> None:
    product: ProductTuple = (uuid7(), Decimal("4.50"), "Test Product", product_status)
    product_model = ProductModel(*product)
    async with session.begin():
        session.add(product_model)

    product_update = {
        "monthly_fee_in_euros": str(product[1]),
        "name": "Updated Product",
        "status": product_status,
    }
    response = await client.put(f"/products/{product[0]}", json=product_update)

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {
        "detail": f"Cannot modify non-status attributes of a {product_status} product"
    }

    async with session.begin():
        products_in_database = await _get_products_from_database(session)
    assert products_in_database == [product]


async def test_update_product_modifies_product_in_database(
    client: AsyncClient, session: AsyncSession
) -> None:
    products: ProductTuples = (
        (uuid7(), Decimal("1.00"), "Original Product", "draft"),
        (uuid7(), Decimal("2.00"), "Other Product", "draft"),
    )
    product_models = tuple(ProductModel(*product) for product in products)
    async with session.begin():
        session.add_all(product_models)

    new_name = "Updated Product"
    new_status = "published"
    product_update = {
        "monthly_fee_in_euros": str(products[0][1]),
        "name": new_name,
        "status": new_status,
    }
    response = await client.put(f"/products/{products[0][0]}", json=product_update)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"id": str(products[0][0])} | product_update

    async with session.begin():
        products_in_database = await _get_products_from_database(session)
    assert sorted(products_in_database) == sorted(
        (
            (products[0][0], products[0][1], new_name, new_status),
            products[1],
        )
    )


@pytest.mark.parametrize(
    ("initial_status", "target_status"),
    [("published", "draft"), ("deprecated", "draft"), ("deprecated", "published")],
)
async def test_update_product_status_forbidden_transitions_fail(
    client: AsyncClient,
    session: AsyncSession,
    initial_status: ProductStatus,
    target_status: ProductStatus,
) -> None:
    product: ProductTuple = (uuid7(), Decimal("3.33"), "Test Product", initial_status)
    product_model = ProductModel(*product)
    async with session.begin():
        session.add(product_model)

    response = await client.put(
        f"/products/{product[0]}",
        json={
            "monthly_fee_in_euros": str(product[1]),
            "name": product[2],
            "status": target_status,
        },
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {
        "detail": f"Cannot change status from {initial_status} to {target_status}"
    }

    async with session.begin():
        products_in_database = await _get_products_from_database(session)
    assert products_in_database == [product]


async def test_update_product_with_existing_name_fails(
    client: AsyncClient, session: AsyncSession
) -> None:
    products: ProductTuples = (
        (uuid7(), Decimal("1.10"), "Original Product", "draft"),
        (uuid7(), Decimal("1.20"), "Existing Product", "draft"),
    )
    product_models = tuple(ProductModel(*product) for product in products)
    async with session.begin():
        session.add_all(product_models)

    response = await client.put(
        f"/products/{products[0][0]}",
        json={
            "monthly_fee_in_euros": str(products[0][1]),
            "name": products[1][2],
            "status": "published",
        },
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {
        "detail": f"Product with name '{products[1][2]}' already exists."
    }

    async with session.begin():
        products_in_database = await _get_products_from_database(session)
    assert sorted(products_in_database) == sorted(products)


async def test_update_product_with_nonexistent_id_fails(
    client: AsyncClient, session: AsyncSession
) -> None:
    product: ProductTuple = (
        uuid7(),
        Decimal("5.55"),
        "Test Product",
        "published",
    )
    product_model = ProductModel(*product)
    async with session.begin():
        session.add(product_model)

    nonexistent_product_id = uuid7()
    response = await client.put(
        f"/products/{nonexistent_product_id}",
        json={
            "monthly_fee_in_euros": "9.99",
            "name": "Updated Product",
            "status": "published",
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"Product with ID {nonexistent_product_id} does not exist."
    }

    async with session.begin():
        products_in_database = await _get_products_from_database(session)
    assert products_in_database == [product]


@pytest.mark.parametrize("product_status", ["draft", "published", "deprecated"])
async def test_update_product_without_changes_succeeds(
    client: AsyncClient,
    session: AsyncSession,
    product_status: ProductStatus,
    to_product_dict: ToProductDict,
) -> None:
    product: ProductTuple = (uuid7(), Decimal("7.77"), "Test Product", product_status)
    product_model = ProductModel(*product)
    async with session.begin():
        session.add(product_model)

    response = await client.put(
        f"/products/{product[0]}",
        json={
            "monthly_fee_in_euros": str(product[1]),
            "name": product[2],
            "status": product[3],
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == to_product_dict(product)

    async with session.begin():
        products_in_database = await _get_products_from_database(session)
    assert products_in_database == [product]
