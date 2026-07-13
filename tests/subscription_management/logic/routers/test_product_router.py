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
from subscription_management.logic.repositories.product_repository import (
    ProductRepository,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession

type _JsonObject = dict[str, object]


def _get_id(json_object: _JsonObject) -> str:
    return str(json_object["id"])


async def _insert_products(session: AsyncSession, *products: Product) -> None:
    async with session.begin():
        product_repository = ProductRepository(_session=session)
        for product in products:
            result = await product_repository.create_product(product)
            assert result[0] == "success"


async def _select_products(session: AsyncSession) -> tuple[Product, ...]:
    async with session.begin():
        product_repository = ProductRepository(_session=session)
        return await product_repository.read_products()


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


async def test_create_product_adds_additional_product_to_database(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    products = (
        Product(
            id=uuid7(),
            monthly_fee_in_euros=Decimal("6.99"),
            name="Product 1",
            status="published",
        ),
        Product(
            id=uuid7(),
            monthly_fee_in_euros=Decimal("3.25"),
            name="Product 2",
            status="published",
        ),
    )
    await _insert_products(session, *products)

    additional_product = Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("9.99"),
        name="Product 3",
        status="published",
    )
    response = await client.post(
        "/products/", json=_to_product_json(additional_product)
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == _to_product_json(additional_product)

    products_in_database = await _select_products(session)
    assert frozenset(products_in_database) == frozenset((*products, additional_product))


async def test_create_product_with_existing_id_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    product = Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("5.99"),
        name="Test Product",
        status="published",
    )
    await _insert_products(session, product)

    conflicting_product = Product(
        id=product.id,
        monthly_fee_in_euros=Decimal("8.49"),
        name="Different Product",
        status="published",
    )
    response = await client.post(
        "/products/", json=_to_product_json(conflicting_product)
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {
        "detail": f"Product with ID {product.id} already exists."
    }

    products_in_database = await _select_products(session)
    assert products_in_database == (product,)


async def test_create_product_with_existing_name_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    product = Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("5.99"),
        name="Test Product",
        status="published",
    )
    await _insert_products(session, product)

    conflicting_product = Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("8.49"),
        name=product.name,
        status="published",
    )
    response = await client.post(
        "/products/", json=_to_product_json(conflicting_product)
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {
        "detail": f"Product with name {product.name} already exists."
    }

    products_in_database = await _select_products(session)
    assert products_in_database == (product,)


async def test_delete_product_removes_draft_product_from_database(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    products = (
        Product(
            id=uuid7(),
            monthly_fee_in_euros=Decimal("0.89"),
            name="Product 1",
            status="draft",
        ),
        Product(
            id=uuid7(),
            monthly_fee_in_euros=Decimal("0.69"),
            name="Product 2",
            status="published",
        ),
    )
    await _insert_products(session, *products)

    response = await client.delete(f"/products/{products[0].id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.content == b""

    products_in_database = await _select_products(session)
    assert products_in_database == (products[1],)


async def test_delete_product_with_nonexistent_id_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    product = Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("2.99"),
        name="Test Product",
        status="published",
    )
    await _insert_products(session, product)

    nonexistent_product_id = uuid7()
    response = await client.delete(f"/products/{nonexistent_product_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"Product with ID {nonexistent_product_id} does not exist."
    }

    products_in_database = await _select_products(session)
    assert products_in_database == (product,)


@pytest.mark.parametrize("product_status", ["published", "deprecated"])
async def test_delete_product_with_non_draft_status_fails(
    client: AsyncClient,
    session: AsyncSession,
    product_status: ProductStatus,
) -> None:
    product = Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("3.99"),
        name="Test Product",
        status=product_status,
    )
    await _insert_products(session, product)

    response = await client.delete(f"/products/{product.id}")

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {
        "detail": (
            f"Product with ID {product.id} cannot be deleted "
            f"because its status is {product_status}."
        )
    }

    products_in_database = await _select_products(session)
    assert products_in_database == (product,)


async def test_read_product_by_id_returns_product(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    product = Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("1.99"),
        name="Test Product",
        status="published",
    )
    await _insert_products(session, product)

    response = await client.get(f"/products/{product.id}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == _to_product_json(product)


async def test_read_product_by_id_with_nonexistent_id_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    product = Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("1.99"),
        name="Test Product",
        status="published",
    )
    await _insert_products(session, product)

    nonexistent_product_id = uuid7()
    response = await client.get(f"/products/{nonexistent_product_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"Product with ID {nonexistent_product_id} does not exist."
    }


async def test_read_product_by_name_returns_product(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    product = Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("1.99"),
        name="Test Product",
        status="published",
    )
    await _insert_products(session, product)

    response = await client.get(f"/products/by-name/{product.name}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == _to_product_json(product)


async def test_read_product_by_name_with_nonexistent_name_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    product = Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("1.99"),
        name="Test Product",
        status="published",
    )
    await _insert_products(session, product)

    nonexistent_product_name = "Nonexistent Product"
    response = await client.get(f"/products/by-name/{nonexistent_product_name}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"Product with name {nonexistent_product_name} does not exist."
    }


async def test_read_products_returns_all_products(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    products = (
        Product(
            id=uuid7(),
            monthly_fee_in_euros=Decimal("4.99"),
            name="Product 1",
            status="published",
        ),
        Product(
            id=uuid7(),
            monthly_fee_in_euros=Decimal("2.99"),
            name="Product 2",
            status="published",
        ),
    )
    await _insert_products(session, *products)

    response = await client.get("/products/")

    assert response.status_code == status.HTTP_200_OK
    assert _sorted_by_id(response.json()) == _sorted_by_id(
        _to_product_json(product) for product in products
    )


async def test_read_products_returns_empty_list_when_no_products(
    client: AsyncClient,
) -> None:
    response = await client.get("/products/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


@pytest.mark.parametrize("product_status", ["published", "deprecated"])
async def test_update_product_cannot_change_non_status_attributes_of_published_product(
    client: AsyncClient,
    session: AsyncSession,
    product_status: ProductStatus,
) -> None:
    product = Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("4.50"),
        name="Test Product",
        status=product_status,
    )
    await _insert_products(session, product)

    product_update = {
        "monthly_fee_in_euros": str(product.monthly_fee_in_euros),
        "name": "Updated Product",
        "status": product_status,
    }
    response = await client.put(f"/products/{product.id}", json=product_update)

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {
        "detail": f"Cannot modify non-status attributes of a {product_status} product"
    }

    products_in_database = await _select_products(session)
    assert products_in_database == (product,)


async def test_update_product_modifies_product_in_database(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    products = (
        Product(
            id=uuid7(),
            monthly_fee_in_euros=Decimal("1.00"),
            name="Original Product",
            status="draft",
        ),
        Product(
            id=uuid7(),
            monthly_fee_in_euros=Decimal("2.00"),
            name="Other Product",
            status="draft",
        ),
    )
    await _insert_products(session, *products)

    new_name = "Updated Product"
    new_status: ProductStatus = "published"
    product_update = {
        "monthly_fee_in_euros": str(products[0].monthly_fee_in_euros),
        "name": new_name,
        "status": new_status,
    }
    response = await client.put(f"/products/{products[0].id}", json=product_update)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"id": str(products[0].id)} | product_update

    updated_product = dataclasses.replace(products[0], name=new_name, status=new_status)
    products_in_database = await _select_products(session)
    assert frozenset(products_in_database) == frozenset((updated_product, products[1]))


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
    product = Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("3.33"),
        name="Test Product",
        status=initial_status,
    )
    await _insert_products(session, product)

    response = await client.put(
        f"/products/{product.id}",
        json={
            "monthly_fee_in_euros": str(product.monthly_fee_in_euros),
            "name": product.name,
            "status": target_status,
        },
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {
        "detail": f"Cannot change status from {initial_status} to {target_status}"
    }

    products_in_database = await _select_products(session)
    assert products_in_database == (product,)


async def test_update_product_with_existing_name_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    products = (
        Product(
            id=uuid7(),
            monthly_fee_in_euros=Decimal("1.10"),
            name="Original Product",
            status="draft",
        ),
        Product(
            id=uuid7(),
            monthly_fee_in_euros=Decimal("1.20"),
            name="Existing Product",
            status="draft",
        ),
    )
    await _insert_products(session, *products)

    response = await client.put(
        f"/products/{products[0].id}",
        json={
            "monthly_fee_in_euros": str(products[0].monthly_fee_in_euros),
            "name": products[1].name,
            "status": "published",
        },
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {
        "detail": f"Product with name '{products[1].name}' already exists."
    }

    products_in_database = await _select_products(session)
    assert frozenset(products_in_database) == frozenset(products)


async def test_update_product_with_nonexistent_id_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    product = Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("5.55"),
        name="Test Product",
        status="published",
    )
    await _insert_products(session, product)

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

    products_in_database = await _select_products(session)
    assert products_in_database == (product,)


@pytest.mark.parametrize("product_status", ["draft", "published", "deprecated"])
async def test_update_product_without_changes_succeeds(
    client: AsyncClient,
    session: AsyncSession,
    product_status: ProductStatus,
) -> None:
    product = Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("7.77"),
        name="Test Product",
        status=product_status,
    )
    await _insert_products(session, product)

    response = await client.put(
        f"/products/{product.id}",
        json=_to_product_json_without_id(product),
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == _to_product_json(product)

    products_in_database = await _select_products(session)
    assert products_in_database == (product,)
