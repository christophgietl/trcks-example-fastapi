from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, Literal, final

from fastapi import Depends
from sqlalchemy import delete, insert, select, update
from sqlalchemy.exc import IntegrityError
from trcks.oop import AwaitableTupleWrapper, Wrapper

from app.data_structures.models import ProductModel
from app.logic.database import AsyncSessionDep  # noqa: TC001

if TYPE_CHECKING:
    from collections.abc import Awaitable
    from uuid import UUID

    from trcks import AwaitableResult, AwaitableTuple, Result

    from app.data_structures.domain.product import Product

type _AwaitableBaseProductResult = Awaitable[_BaseProductResult]
type _BaseProductResult = Result[Literal["Product does not exist"], Product]

type ProductRepositoryDep = Annotated[ProductRepository, Depends()]


@final
@dataclass(frozen=True, kw_only=True, slots=True)
class ProductRepository:
    _session: AsyncSessionDep

    async def _create_product_model(
        self, product: Product
    ) -> Result[Literal["ID already exists", "Name already exists"], ProductModel]:
        statement = (
            insert(ProductModel)
            .values(
                id=product.id,
                monthly_fee_in_euros=product.monthly_fee_in_euros,
                name=product.name,
                status=product.status,
            )
            .returning(ProductModel)
        )
        try:
            scalars = await self._session.scalars(statement=statement)
        except IntegrityError as e:
            match str(e.orig):
                case "UNIQUE constraint failed: product.id":
                    return "failure", "ID already exists"
                case "UNIQUE constraint failed: product.name":
                    return "failure", "Name already exists"
                case _:  # pragma: no cover
                    raise
        else:
            return "success", scalars.one()

    async def _delete_product_model(self, id_: UUID) -> ProductModel | None:
        statement = (
            delete(ProductModel).where(ProductModel.id == id_).returning(ProductModel)
        )
        return await self._session.scalar(statement=statement)

    async def _read_product_model_by_id(self, id_: UUID) -> ProductModel | None:
        return await self._session.get(ProductModel, id_)

    async def _read_product_model_by_name(self, name: str) -> ProductModel | None:
        statement = select(ProductModel).where(ProductModel.name == name)
        return await self._session.scalar(statement=statement)

    async def _read_product_models(self) -> tuple[ProductModel, ...]:
        statement = select(ProductModel)
        scalars = await self._session.scalars(statement=statement)
        return tuple(scalars.all())

    @staticmethod
    def _to_base_product_result(
        product_model: ProductModel | None,
    ) -> _BaseProductResult:
        if product_model is None:
            return "failure", "Product does not exist"
        return "success", product_model.to_product()

    async def _update_product_model(
        self, product: Product
    ) -> Result[Literal["Name already exists"], ProductModel | None]:
        statement = (
            update(ProductModel)
            .where(ProductModel.id == product.id)
            .values(
                monthly_fee_in_euros=product.monthly_fee_in_euros,
                name=product.name,
                status=product.status,
            )
            .returning(ProductModel)
        )
        try:
            updated_product_model = await self._session.scalar(statement=statement)
        except IntegrityError as e:
            match str(e.orig):
                case "UNIQUE constraint failed: product.name":
                    return "failure", "Name already exists"
                case _:  # pragma: no cover
                    raise
        else:
            return "success", updated_product_model

    def create_product(
        self, product: Product
    ) -> AwaitableResult[Literal["ID already exists", "Name already exists"], Product]:
        return (
            Wrapper(product)
            .map_to_awaitable_result(self._create_product_model)
            .map_success(ProductModel.to_product)
            .core
        )

    def delete_product(self, id_: UUID) -> _AwaitableBaseProductResult:
        return (
            Wrapper(id_)
            .map_to_awaitable(self._delete_product_model)
            .map(self._to_base_product_result)
            .core
        )

    def read_product_by_id(self, id_: UUID) -> _AwaitableBaseProductResult:
        return (
            Wrapper(id_)
            .map_to_awaitable(self._read_product_model_by_id)
            .map(self._to_base_product_result)
            .core
        )

    def read_product_by_name(self, name: str) -> _AwaitableBaseProductResult:
        return (
            Wrapper(name)
            .map_to_awaitable(self._read_product_model_by_name)
            .map(self._to_base_product_result)
            .core
        )

    def read_products(self) -> AwaitableTuple[Product]:
        return (
            AwaitableTupleWrapper(self._read_product_models())
            .map(ProductModel.to_product)
            .core
        )

    def update_product(
        self, product: Product
    ) -> AwaitableResult[
        Literal["Name already exists", "Product does not exist"], Product
    ]:
        return (
            Wrapper(product)
            .map_to_awaitable_result(self._update_product_model)
            .map_success_to_result(self._to_base_product_result)
            .core
        )
