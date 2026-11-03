import dataclasses
from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, Literal, cast, final

from fastapi import Depends
from trcks.oop import Wrapper

from subscription_management.data_structures.domain.product import ProductStatus
from subscription_management.data_structures.domain.product_error import (
    ProductNotDeletableBecauseStatusError,
    ProductPayloadNotUpdatableBecauseStatusError,
    ProductStatusTransitionNotAllowedError,
    ProductWithIdAlreadyExistsError,
    ProductWithIdDoesNotExistError,
    ProductWithNameAlreadyExistsError,
    ProductWithNameDoesNotExistError,
)
from subscription_management.logic.repositories.product_repository import (
    ProductRepositoryDep,  # noqa: TC001
)

if TYPE_CHECKING:
    from uuid import UUID

    from trcks import AwaitableResult, AwaitableTuple, Result

    from subscription_management.data_structures.domain.product import Product

type _DeleteProductError = (
    ProductNotDeletableBecauseStatusError | ProductWithIdDoesNotExistError
)
type _UpdateNotAllowedError = (
    ProductPayloadNotUpdatableBecauseStatusError
    | ProductStatusTransitionNotAllowedError
    | ProductWithIdDoesNotExistError
)

type ProductServiceDep = Annotated[ProductService, Depends()]


@final
@dataclass(frozen=True, slots=True)
class _ProductUpdate:
    before: Product
    after: Product


@final
@dataclass(frozen=True, kw_only=True, slots=True)
class ProductService:
    _product_repository: ProductRepositoryDep

    def _add_old_product(
        self, new_product: Product
    ) -> AwaitableResult[ProductWithIdDoesNotExistError, _ProductUpdate]:
        return (
            Wrapper(new_product.id)
            .map_to_awaitable_result(self.read_product_by_id)
            .map_success(_ProductUpdate, after=new_product)
            .core
        )

    def _ensure_by_id_that_product_can_be_deleted(
        self, id_: UUID
    ) -> AwaitableResult[_DeleteProductError, None]:
        return (
            Wrapper(id_)
            .map_to_awaitable_result(self.read_product_by_id)
            .map_success_to_result(self._ensure_that_product_can_be_deleted)
            .core
        )

    @staticmethod
    def _ensure_that_payload_update_is_allowed(
        product_update: _ProductUpdate,
    ) -> Result[ProductPayloadNotUpdatableBecauseStatusError, None]:
        if product_update.before.status == ProductStatus.DRAFT:
            return "success", None

        payload_is_identical = product_update.before == dataclasses.replace(
            product_update.after, status=product_update.before.status
        )
        if payload_is_identical:
            return "success", None

        return "failure", ProductPayloadNotUpdatableBecauseStatusError(
            id=product_update.before.id,
            status=product_update.before.status,
        )

    @staticmethod
    def _ensure_that_product_can_be_deleted(
        product: Product,
    ) -> Result[
        ProductNotDeletableBecauseStatusError,
        None,
    ]:
        if product.status == ProductStatus.DRAFT:
            return "success", None
        return "failure", ProductNotDeletableBecauseStatusError(
            id=product.id, status=product.status
        )

    @staticmethod
    def _ensure_that_status_update_is_allowed(
        product_update: _ProductUpdate,
    ) -> Result[ProductStatusTransitionNotAllowedError, None]:
        if product_update.before.status > product_update.after.status:
            return "failure", ProductStatusTransitionNotAllowedError(
                id=product_update.before.id,
                before=cast(
                    "Literal[ProductStatus.PUBLISHED, ProductStatus.DEPRECATED]",
                    product_update.before.status,
                ),
                after=cast(
                    "Literal[ProductStatus.DRAFT, ProductStatus.PUBLISHED]",
                    product_update.after.status,
                ),
            )
        return "success", None

    def _ensure_that_update_is_allowed(
        self, new_product: Product
    ) -> AwaitableResult[_UpdateNotAllowedError, None]:
        return (
            Wrapper(new_product)
            .map_to_awaitable_result(self._add_old_product)
            .tap_success_to_result(self._ensure_that_status_update_is_allowed)
            .tap_success_to_result(self._ensure_that_payload_update_is_allowed)
            .map_success(lambda _: None)
            .core
        )

    def create_product(
        self, product: Product
    ) -> AwaitableResult[
        ProductWithIdAlreadyExistsError | ProductWithNameAlreadyExistsError, Product
    ]:
        return self._product_repository.create_product(product)

    def delete_product(
        self, id_: UUID
    ) -> AwaitableResult[_DeleteProductError, Product]:
        return (
            Wrapper(id_)
            .tap_to_awaitable_result(self._ensure_by_id_that_product_can_be_deleted)
            .map_success_to_awaitable_result(self._product_repository.delete_product)
            .core
        )

    def read_product_by_id(
        self, id_: UUID
    ) -> AwaitableResult[ProductWithIdDoesNotExistError, Product]:
        return self._product_repository.read_product_by_id(id_)

    def read_product_by_name(
        self, name: str
    ) -> AwaitableResult[ProductWithNameDoesNotExistError, Product]:
        return self._product_repository.read_product_by_name(name)

    def read_products(self) -> AwaitableTuple[Product]:
        return self._product_repository.read_products()

    def update_product(
        self, product: Product
    ) -> AwaitableResult[
        _UpdateNotAllowedError | ProductWithNameAlreadyExistsError,
        Product,
    ]:
        return (
            Wrapper(product)
            .tap_to_awaitable_result(self._ensure_that_update_is_allowed)
            .map_success_to_awaitable_result(self._product_repository.update_product)
            .core
        )
