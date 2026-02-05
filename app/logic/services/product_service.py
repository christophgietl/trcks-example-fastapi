import dataclasses
from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, Literal, assert_never

from fastapi import Depends
from trcks.oop import Wrapper

from app.logic.repositories.product_repository import (
    ProductRepositoryDep,  # noqa: TC001
)

if TYPE_CHECKING:
    from collections.abc import Awaitable
    from uuid import UUID

    from trcks import AwaitableResult, Result

    from app.data_structures.domain.product import Product

type _AwaitableReadProductResult = AwaitableResult[_ProductDoesNotExistLiteral, Product]
type _CannotDeleteProductLiteral = _ProductDoesNotExistLiteral | _ProductStatusLiteral
type _CannotUpdateProductLiteral = (
    _CannotUpdateProductPayloadLiteral
    | _CannotUpdateProductStatusLiteral
    | _ProductDoesNotExistLiteral
)
type _CannotUpdateProductPayloadLiteral = Literal[
    "Cannot modify non-status attributes of a published product",
    "Cannot modify non-status attributes of a deprecated product",
]
type _CannotUpdateProductStatusLiteral = Literal[
    "Cannot change status from published to draft",
    "Cannot change status from deprecated to draft",
    "Cannot change status from deprecated to published",
]
type _ProductDoesNotExistLiteral = Literal["Product does not exist"]
type _ProductStatusLiteral = Literal[
    "Product status is published", "Product status is deprecated"
]

type ProductServiceDep = Annotated[ProductService, Depends()]


@dataclass(frozen=True, kw_only=True, slots=True)
class _ProductUpdate:
    before: Product
    after: Product


@dataclass(frozen=True, kw_only=True, slots=True)
class ProductService:
    _product_repository: ProductRepositoryDep

    def _add_old_product(
        self, new_product: Product
    ) -> AwaitableResult[_ProductDoesNotExistLiteral, _ProductUpdate]:
        return (
            Wrapper(new_product.id)
            .map_to_awaitable_result(self.read_product_by_id)
            .map_success(
                lambda old_product: _ProductUpdate(
                    before=old_product, after=new_product
                )
            )
            .core
        )

    def _check_by_id_that_product_can_be_deleted(
        self, id_: UUID
    ) -> AwaitableResult[_CannotDeleteProductLiteral, None]:
        return (
            Wrapper(id_)
            .map_to_awaitable_result(self.read_product_by_id)
            .map_success_to_result(self._check_that_product_can_be_deleted)
            .core
        )

    @staticmethod
    def _check_that_payload_update_is_allowed(
        product_update: _ProductUpdate,
    ) -> Result[_CannotUpdateProductPayloadLiteral, None]:
        payload_is_identical = product_update.before == dataclasses.replace(
            product_update.after, status=product_update.before.status
        )
        match pair := payload_is_identical, product_update.before.status:
            case True, "draft" | "published" | "deprecated":
                return "success", None
            case False, "draft":
                return "success", None
            case False, "published":
                return (
                    "failure",
                    "Cannot modify non-status attributes of a published product",
                )
            case False, "deprecated":
                return (
                    "failure",
                    "Cannot modify non-status attributes of a deprecated product",
                )
            case _:  # pragma: no cover
                assert_never(pair)

    @staticmethod
    def _check_that_product_can_be_deleted(
        product: Product,
    ) -> Result[_ProductStatusLiteral, None]:
        match product.status:
            case "draft":
                return "success", None
            case "published":
                return "failure", "Product status is published"
            case "deprecated":
                return "failure", "Product status is deprecated"
            case _:  # pragma: no cover
                assert_never(product.status)

    @staticmethod
    def _check_that_status_update_is_allowed(
        product_update: _ProductUpdate,
    ) -> Result[_CannotUpdateProductStatusLiteral, None]:
        match pair := product_update.before.status, product_update.after.status:
            case "draft", "draft" | "published" | "deprecated":
                return "success", None
            case "published", "draft":
                return "failure", "Cannot change status from published to draft"
            case "published", "published" | "deprecated":
                return "success", None
            case "deprecated", "draft":
                return "failure", "Cannot change status from deprecated to draft"
            case "deprecated", "published":
                return "failure", "Cannot change status from deprecated to published"
            case "deprecated", "deprecated":
                return "success", None
            case _:  # pragma: no cover
                assert_never(pair)

    def _check_that_update_is_allowed(
        self, new_product: Product
    ) -> AwaitableResult[_CannotUpdateProductLiteral, None]:
        return (
            Wrapper(new_product)
            .map_to_awaitable_result(self._add_old_product)
            .tap_success_to_result(self._check_that_status_update_is_allowed)
            .tap_success_to_result(self._check_that_payload_update_is_allowed)
            .map_success(lambda _: None)
            .core
        )

    def create_product(
        self, product: Product
    ) -> AwaitableResult[Literal["Name already exists", "ID already exists"], None]:
        return self._product_repository.create_product(product)

    def delete_product(
        self, id_: UUID
    ) -> AwaitableResult[_CannotDeleteProductLiteral, Product]:
        return (
            Wrapper(id_)
            .tap_to_awaitable_result(self._check_by_id_that_product_can_be_deleted)
            .map_success_to_awaitable_result(self._product_repository.delete_product)
            .core
        )

    def read_product_by_id(self, id_: UUID) -> _AwaitableReadProductResult:
        return self._product_repository.read_product_by_id(id_)

    def read_product_by_name(self, name: str) -> _AwaitableReadProductResult:
        return self._product_repository.read_product_by_name(name)

    def read_products(self) -> Awaitable[tuple[Product, ...]]:
        return self._product_repository.read_products()

    def update_product(
        self, product: Product
    ) -> AwaitableResult[
        _CannotUpdateProductLiteral | Literal["Name already exists"],
        Product,
    ]:
        return (
            Wrapper(product)
            .tap_to_awaitable_result(self._check_that_update_is_allowed)
            .map_success_to_awaitable_result(self._product_repository.update_product)
            .core
        )
