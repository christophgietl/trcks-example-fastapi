import dataclasses
from collections.abc import Callable, Iterable, Mapping
from decimal import Decimal
from typing import TYPE_CHECKING, Literal, Self, final
from uuid import UUID, uuid7

import pytest
from fastapi import status
from sqlalchemy import select

from subscription_management.data_structures.models import ProductModel

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


async def test_create_product_adds_additional_product_to_database(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    products = (
        _Product(
            id=uuid7(),
            monthly_fee_in_euros=Decimal("6.99"),
            name="Product 1",
            status="published",
        ),
        _Product(
            id=uuid7(),
            monthly_fee_in_euros=Decimal("3.25"),
            name="Product 2",
            status="published",
        ),
    )
    for product in products:
        await product.insert(session)

    additional_product = _Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("9.99"),
        name="Product 3",
        status="published",
    )
    response = await client.post("/products/", json=additional_product.to_json())

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == additional_product.to_json()

    products_in_database = await _Product.select(session)
    assert sorted(products_in_database) == sorted((*products, additional_product))


async def test_create_product_with_existing_id_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    product = _Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("5.99"),
        name="Test Product",
        status="published",
    )
    await product.insert(session)

    conflicting_product = _Product(
        id=product.id,
        monthly_fee_in_euros=Decimal("8.49"),
        name="Different Product",
        status="published",
    )
    response = await client.post("/products/", json=conflicting_product.to_json())

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {
        "detail": f"Product with ID {product.id} already exists."
    }

    products_in_database = await _Product.select(session)
    assert products_in_database == (product,)


async def test_create_product_with_existing_name_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    product = _Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("5.99"),
        name="Test Product",
        status="published",
    )
    await product.insert(session)

    conflicting_product = _Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("8.49"),
        name=product.name,
        status="published",
    )
    response = await client.post("/products/", json=conflicting_product.to_json())

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {
        "detail": f"Product with name {product.name} already exists."
    }

    products_in_database = await _Product.select(session)
    assert products_in_database == (product,)


async def test_delete_product_removes_draft_product_from_database(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    products = (
        _Product(
            id=uuid7(),
            monthly_fee_in_euros=Decimal("0.89"),
            name="Product 1",
            status="draft",
        ),
        _Product(
            id=uuid7(),
            monthly_fee_in_euros=Decimal("0.69"),
            name="Product 2",
            status="published",
        ),
    )
    for product in products:
        await product.insert(session)

    response = await client.delete(f"/products/{products[0].id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.content == b""

    products_in_database = await _Product.select(session)
    assert products_in_database == (products[1],)


async def test_delete_product_with_nonexistent_id_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    product = _Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("2.99"),
        name="Test Product",
        status="published",
    )
    await product.insert(session)

    nonexistent_product_id = uuid7()
    response = await client.delete(f"/products/{nonexistent_product_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"Product with ID {nonexistent_product_id} does not exist."
    }

    products_in_database = await _Product.select(session)
    assert products_in_database == (product,)


@pytest.mark.parametrize("product_status", ["published", "deprecated"])
async def test_delete_product_with_non_draft_status_fails(
    client: AsyncClient,
    session: AsyncSession,
    product_status: _ProductStatus,
) -> None:
    product = _Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("3.99"),
        name="Test Product",
        status=product_status,
    )
    await product.insert(session)

    response = await client.delete(f"/products/{product.id}")

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {
        "detail": (
            f"Product with ID {product.id} cannot be deleted "
            f"because its status is {product_status}."
        )
    }

    products_in_database = await _Product.select(session)
    assert products_in_database == (product,)


async def test_read_product_by_id_returns_product(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    product = _Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("1.99"),
        name="Test Product",
        status="published",
    )
    await product.insert(session)

    response = await client.get(f"/products/{product.id}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == product.to_json()


async def test_read_product_by_id_with_nonexistent_id_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    product = _Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("1.99"),
        name="Test Product",
        status="published",
    )
    await product.insert(session)

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
    product = _Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("1.99"),
        name="Test Product",
        status="published",
    )
    await product.insert(session)

    response = await client.get(f"/products/by-name/{product.name}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == product.to_json()


async def test_read_product_by_name_with_nonexistent_name_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    product = _Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("1.99"),
        name="Test Product",
        status="published",
    )
    await product.insert(session)

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
) -> None:
    products = (
        _Product(
            id=uuid7(),
            monthly_fee_in_euros=Decimal("4.99"),
            name="Product 1",
            status="published",
        ),
        _Product(
            id=uuid7(),
            monthly_fee_in_euros=Decimal("2.99"),
            name="Product 2",
            status="published",
        ),
    )
    for product in products:
        await product.insert(session)

    response = await client.get("/products/")

    assert response.status_code == status.HTTP_200_OK
    assert sorted_by_id(response.json()) == sorted_by_id(
        product.to_json() for product in products
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
    product_status: _ProductStatus,
) -> None:
    product = _Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("4.50"),
        name="Test Product",
        status=product_status,
    )
    await product.insert(session)

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

    products_in_database = await _Product.select(session)
    assert products_in_database == (product,)


async def test_update_product_modifies_product_in_database(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    products = (
        _Product(
            id=uuid7(),
            monthly_fee_in_euros=Decimal("1.00"),
            name="Original Product",
            status="draft",
        ),
        _Product(
            id=uuid7(),
            monthly_fee_in_euros=Decimal("2.00"),
            name="Other Product",
            status="draft",
        ),
    )
    for product in products:
        await product.insert(session)

    new_name = "Updated Product"
    new_status: _ProductStatus = "published"
    product_update = {
        "monthly_fee_in_euros": str(products[0].monthly_fee_in_euros),
        "name": new_name,
        "status": new_status,
    }
    response = await client.put(f"/products/{products[0].id}", json=product_update)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"id": str(products[0].id)} | product_update

    updated_product = dataclasses.replace(products[0], name=new_name, status=new_status)
    products_in_database = await _Product.select(session)
    assert sorted(products_in_database) == sorted((updated_product, products[1]))


@pytest.mark.parametrize(
    ("initial_status", "target_status"),
    [("published", "draft"), ("deprecated", "draft"), ("deprecated", "published")],
)
async def test_update_product_status_forbidden_transitions_fail(
    client: AsyncClient,
    session: AsyncSession,
    initial_status: _ProductStatus,
    target_status: _ProductStatus,
) -> None:
    product = _Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("3.33"),
        name="Test Product",
        status=initial_status,
    )
    await product.insert(session)

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

    products_in_database = await _Product.select(session)
    assert products_in_database == (product,)


async def test_update_product_with_existing_name_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    products = (
        _Product(
            id=uuid7(),
            monthly_fee_in_euros=Decimal("1.10"),
            name="Original Product",
            status="draft",
        ),
        _Product(
            id=uuid7(),
            monthly_fee_in_euros=Decimal("1.20"),
            name="Existing Product",
            status="draft",
        ),
    )
    for product in products:
        await product.insert(session)

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

    products_in_database = await _Product.select(session)
    assert sorted(products_in_database) == sorted(products)


async def test_update_product_with_nonexistent_id_fails(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    product = _Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("5.55"),
        name="Test Product",
        status="published",
    )
    await product.insert(session)

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

    products_in_database = await _Product.select(session)
    assert products_in_database == (product,)


@pytest.mark.parametrize("product_status", ["draft", "published", "deprecated"])
async def test_update_product_without_changes_succeeds(
    client: AsyncClient,
    session: AsyncSession,
    product_status: _ProductStatus,
) -> None:
    product = _Product(
        id=uuid7(),
        monthly_fee_in_euros=Decimal("7.77"),
        name="Test Product",
        status=product_status,
    )
    await product.insert(session)

    response = await client.put(
        f"/products/{product.id}",
        json=product.to_json_without_id(),
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == product.to_json()

    products_in_database = await _Product.select(session)
    assert products_in_database == (product,)
