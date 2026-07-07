from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, final

from fastapi import Depends
from sqlalchemy import delete, insert, select, update
from sqlalchemy.exc import IntegrityError
from trcks.oop import AwaitableTupleWrapper, Wrapper

from subscription_management.data_structures.domain.product_error import (
    ProductWithIdAlreadyExistsError,
    ProductWithIdDoesNotExistError,
    ProductWithNameAlreadyExistsError,
    ProductWithNameDoesNotExistError,
)
from subscription_management.data_structures.models import ProductModel
from subscription_management.logic.database import AsyncSessionDep  # noqa: TC001

if TYPE_CHECKING:
    from uuid import UUID

    from trcks import AwaitableResult, AwaitableTuple, Result

    from subscription_management.data_structures.domain.product import Product

type _ProductByIdResult = Result[ProductWithIdDoesNotExistError, Product]
type _ProductByNameResult = Result[ProductWithNameDoesNotExistError, Product]

type ProductRepositoryDep = Annotated[ProductRepository, Depends()]


@final
@dataclass(frozen=True, kw_only=True, slots=True)
class ProductRepository:
    _session: AsyncSessionDep

    async def _create_product_model(
        self, product: Product
    ) -> Result[
        ProductWithIdAlreadyExistsError | ProductWithNameAlreadyExistsError,
        ProductModel,
    ]:
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
                    return "failure", ProductWithIdAlreadyExistsError(id=product.id)
                case "UNIQUE constraint failed: product.name":
                    return "failure", ProductWithNameAlreadyExistsError(
                        name=product.name
                    )
                case _:  # pragma: no cover
                    raise
        else:
            return "success", scalars.one()

    async def _read_product_models(self) -> tuple[ProductModel, ...]:
        statement = select(ProductModel)
        scalars = await self._session.scalars(statement=statement)
        return tuple(scalars.all())

    def create_product(
        self, product: Product
    ) -> AwaitableResult[
        ProductWithIdAlreadyExistsError | ProductWithNameAlreadyExistsError, Product
    ]:
        return (
            Wrapper(product)
            .map_to_awaitable_result(self._create_product_model)
            .map_success(ProductModel.to_product)
            .core
        )

    async def delete_product(self, id_: UUID) -> _ProductByIdResult:
        statement = (
            delete(ProductModel).where(ProductModel.id == id_).returning(ProductModel)
        )
        product_model = await self._session.scalar(statement=statement)
        if product_model is None:
            return "failure", ProductWithIdDoesNotExistError(id=id_)  # pragma: no cover
        return "success", product_model.to_product()

    async def read_product_by_id(self, id_: UUID) -> _ProductByIdResult:
        product_model = await self._session.get(ProductModel, id_)
        if product_model is None:
            return "failure", ProductWithIdDoesNotExistError(id=id_)
        return "success", product_model.to_product()

    async def read_product_by_name(self, name: str) -> _ProductByNameResult:
        statement = select(ProductModel).where(ProductModel.name == name)
        product_model = await self._session.scalar(statement=statement)
        if product_model is None:
            return "failure", ProductWithNameDoesNotExistError(name=name)
        return "success", product_model.to_product()

    def read_products(self) -> AwaitableTuple[Product]:
        return (
            AwaitableTupleWrapper(self._read_product_models())
            .map(ProductModel.to_product)
            .core
        )

    async def update_product(
        self, product: Product
    ) -> Result[
        ProductWithIdDoesNotExistError | ProductWithNameAlreadyExistsError, Product
    ]:
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
                    return "failure", ProductWithNameAlreadyExistsError(
                        name=product.name
                    )
                case _:  # pragma: no cover
                    raise
        else:
            if updated_product_model is None:
                return "failure", ProductWithIdDoesNotExistError(
                    id=product.id
                )  # pragma: no cover
            return "success", updated_product_model.to_product()
