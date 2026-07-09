import dataclasses
from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, assert_never, final

from fastapi import Depends
from trcks.oop import Wrapper

from subscription_management.data_structures.domain.product_error import (
    ProductPayloadUpdateError,
    ProductStatusDeprecatedError,
    ProductStatusPublishedError,
    ProductStatusUpdateError,
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
    ProductStatusDeprecatedError
    | ProductStatusPublishedError
    | ProductWithIdDoesNotExistError
)
type _UpdateNotAllowedError = (
    ProductPayloadUpdateError
    | ProductStatusUpdateError
    | ProductWithIdDoesNotExistError
)

type ProductServiceDep = Annotated[ProductService, Depends()]


@final
@dataclass(frozen=True, kw_only=True, slots=True)
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
            .map_success(
                lambda old_product: _ProductUpdate(
                    before=old_product, after=new_product
                )
            )
            .core
        )

    def _check_by_id_that_product_can_be_deleted(
        self, id_: UUID
    ) -> AwaitableResult[_DeleteProductError, None]:
        return (
            Wrapper(id_)
            .map_to_awaitable_result(self.read_product_by_id)
            .map_success_to_result(self._check_that_product_can_be_deleted)
            .core
        )

    @staticmethod
    def _check_that_payload_update_is_allowed(
        product_update: _ProductUpdate,
    ) -> Result[ProductPayloadUpdateError, None]:
        payload_is_identical = product_update.before == dataclasses.replace(
            product_update.after, status=product_update.before.status
        )
        match payload_is_identical, product_update.before.status:
            case True, "draft" | "published" | "deprecated":
                return "success", None
            case False, "draft":
                return "success", None
            case False, "published":
                reason = "Cannot modify non-status attributes of a published product"
                error = ProductPayloadUpdateError(
                    reason=reason, status=product_update.before.status
                )
                return "failure", error
            case False, "deprecated":
                reason = "Cannot modify non-status attributes of a deprecated product"
                error = ProductPayloadUpdateError(
                    reason=reason, status=product_update.before.status
                )
                return "failure", error
            case _ as pair:  # pragma: no cover
                assert_never(pair)  # pyright: ignore[reportUnreachable]

    @staticmethod
    def _check_that_product_can_be_deleted(
        product: Product,
    ) -> Result[ProductStatusDeprecatedError | ProductStatusPublishedError, None]:
        match product.status:
            case "draft":
                return "success", None
            case "published":
                return "failure", ProductStatusPublishedError(id=product.id)
            case "deprecated":
                return "failure", ProductStatusDeprecatedError(id=product.id)
            case _:  # pragma: no cover
                assert_never(product.status)  # pyright: ignore[reportUnreachable]

    @staticmethod
    def _check_that_status_update_is_allowed(
        product_update: _ProductUpdate,
    ) -> Result[ProductStatusUpdateError, None]:
        match product_update.before.status, product_update.after.status:
            case "draft", "draft" | "published" | "deprecated":
                return "success", None
            case "published", "draft":
                error = ProductStatusUpdateError(
                    reason="Cannot change status from published to draft",
                    before=product_update.before.status,
                    after=product_update.after.status,
                )
                return "failure", error
            case "published", "published" | "deprecated":
                return "success", None
            case "deprecated", "draft":
                error = ProductStatusUpdateError(
                    reason="Cannot change status from deprecated to draft",
                    before=product_update.before.status,
                    after=product_update.after.status,
                )
                return "failure", error
            case "deprecated", "published":
                error = ProductStatusUpdateError(
                    reason="Cannot change status from deprecated to published",
                    before=product_update.before.status,
                    after=product_update.after.status,
                )
                return "failure", error
            case "deprecated", "deprecated":
                return "success", None
            case _ as pair:  # pragma: no cover
                assert_never(pair)  # pyright: ignore[reportUnreachable]

    def _check_that_update_is_allowed(
        self, new_product: Product
    ) -> AwaitableResult[_UpdateNotAllowedError, None]:
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
    ) -> AwaitableResult[
        ProductWithIdAlreadyExistsError | ProductWithNameAlreadyExistsError, Product
    ]:
        return self._product_repository.create_product(product)

    def delete_product(
        self, id_: UUID
    ) -> AwaitableResult[_DeleteProductError, Product]:
        return (
            Wrapper(id_)
            .tap_to_awaitable_result(self._check_by_id_that_product_can_be_deleted)
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
            .tap_to_awaitable_result(self._check_that_update_is_allowed)
            .map_success_to_awaitable_result(self._product_repository.update_product)
            .core
        )
