from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, Literal, TypeAlias

from fastapi import Depends
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError

from app.data_structures.models import ProductModel
from app.database import AsyncSessionDep  # noqa: TC001

if TYPE_CHECKING:
    from uuid import UUID

    from trcks import Failure, Result

    from app.data_structures.domain.product import Product

type _BaseProductResult = Result[Literal["Product does not exist"], Product]


@dataclass(frozen=True, kw_only=True, slots=True)
class ProductRepository:
    _session: AsyncSessionDep

    @staticmethod
    def _to_base_product_result(
        product_model: ProductModel | None,
    ) -> _BaseProductResult:
        if product_model is None:
            return "failure", "Product does not exist"
        return "success", product_model.to_product()

    async def create_product(
        self, product: Product
    ) -> Result[Literal["Name already exists", "ID already exists"], None]:
        product_model = ProductModel.from_product(product)
        self._session.add(product_model)
        try:
            await self._session.flush()
        except IntegrityError as e:
            match str(e.orig):
                case "UNIQUE constraint failed: product.id":
                    return "failure", "ID already exists"
                case "UNIQUE constraint failed: product.name":
                    return "failure", "Name already exists"
                case _:  # pragma: no cover
                    raise
        else:
            return "success", None

    async def delete_product(self, id_: UUID) -> _BaseProductResult:
        deleted_product_model = await self._session.scalar(
            delete(ProductModel).where(ProductModel.id == id_).returning(ProductModel)
        )
        return self._to_base_product_result(deleted_product_model)

    async def read_product_by_id(self, id_: UUID) -> _BaseProductResult:
        product_model = await self._session.get(ProductModel, id_)
        return self._to_base_product_result(product_model)

    async def read_product_by_name(self, name: str) -> _BaseProductResult:
        product_model = await self._session.scalar(
            select(ProductModel).where(ProductModel.name == name)
        )
        return self._to_base_product_result(product_model)

    async def read_products(self) -> tuple[Product, ...]:
        scalars = await self._session.scalars(select(ProductModel))
        product_models = scalars.all()
        return tuple(product_model.to_product() for product_model in product_models)

    async def update_product(
        self, product: Product
    ) -> _BaseProductResult | Failure[Literal["Name already exists"]]:
        try:
            updated_product_model = await self._session.scalar(
                update(ProductModel)
                .where(ProductModel.id == product.id)
                .values(name=product.name, status=product.status)
                .returning(ProductModel)
            )
        except IntegrityError as e:
            match str(e.orig):
                case "UNIQUE constraint failed: product.name":
                    return "failure", "Name already exists"
                case _:  # pragma: no cover
                    raise
        else:
            return self._to_base_product_result(updated_product_model)


# FastAPI does not support the type keyword when used for dependencies
# as of October 2025 (see https://github.com/fastapi/fastapi/issues/10719):
ProductRepositoryDep: TypeAlias = Annotated[ProductRepository, Depends()]  # noqa: UP040
