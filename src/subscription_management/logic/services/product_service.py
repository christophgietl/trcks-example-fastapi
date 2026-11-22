import dataclasses
from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, assert_never, final

from fastapi import Depends
from trcks.oop import Wrapper

from subscription_management.data_structures.domain.do_not_update import (
    DO_NOT_UPDATE,
)
from subscription_management.data_structures.domain.product import Product
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

    from subscription_management.data_structures.domain.product import ProductUpdate

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
class _BeforeProductAndAfterProduct:
    before: Product
    after: Product


@final
@dataclass(frozen=True, kw_only=True, slots=True)
class ProductService:
    _product_repository: ProductRepositoryDep

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
        products: _BeforeProductAndAfterProduct,
    ) -> Result[ProductPayloadNotUpdatableBecauseStatusError, None]:
        if products.before.status == "draft":
            return "success", None

        payload_is_identical = products.before == dataclasses.replace(
            products.after, status=products.before.status
        )
        if payload_is_identical:
            return "success", None

        return "failure", ProductPayloadNotUpdatableBecauseStatusError(
            id=products.before.id,
            status=products.before.status,
        )

    @staticmethod
    def _ensure_that_product_can_be_deleted(
        product: Product,
    ) -> Result[
        ProductNotDeletableBecauseStatusError,
        None,
    ]:
        if product.status == "draft":
            return "success", None
        return "failure", ProductNotDeletableBecauseStatusError(
            id=product.id, status=product.status
        )

    @staticmethod
    def _ensure_that_status_update_is_allowed(
        products: _BeforeProductAndAfterProduct,
    ) -> Result[ProductStatusTransitionNotAllowedError, None]:
        match products.before.status, products.after.status:
            case (
                ("draft", "draft" | "published" | "deprecated")
                | ("published", "published" | "deprecated")
                | ("deprecated", "deprecated")
            ):
                return "success", None
            case ("published", "draft") | ("deprecated", "draft" | "published"):
                return "failure", ProductStatusTransitionNotAllowedError(
                    id=products.before.id,
                    before=products.before.status,
                    after=products.after.status,
                )
            case _ as status_update:  # pragma: no cover
                assert_never(status_update)  # pyright: ignore[reportUnreachable]

    @staticmethod
    def _merge_with_update(
        before: Product, update: ProductUpdate
    ) -> _BeforeProductAndAfterProduct:
        after = Product(
            id=before.id,
            monthly_fee_in_euros=(
                before.monthly_fee_in_euros
                if update.monthly_fee_in_euros is DO_NOT_UPDATE
                else update.monthly_fee_in_euros
            ),
            name=(before.name if update.name is DO_NOT_UPDATE else update.name),
            status=(before.status if update.status is DO_NOT_UPDATE else update.status),
        )
        return _BeforeProductAndAfterProduct(before=before, after=after)

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
        self, update: ProductUpdate
    ) -> AwaitableResult[
        _UpdateNotAllowedError | ProductWithNameAlreadyExistsError,
        Product,
    ]:
        return (
            Wrapper(update.id)
            .map_to_awaitable_result(self.read_product_by_id)
            .map_success(self._merge_with_update, update=update)
            .tap_success_to_result(self._ensure_that_status_update_is_allowed)
            .tap_success_to_result(self._ensure_that_payload_update_is_allowed)
            .map_success_to_awaitable_result(
                lambda products: self._product_repository.update_product(products.after)
            )
            .core
        )
