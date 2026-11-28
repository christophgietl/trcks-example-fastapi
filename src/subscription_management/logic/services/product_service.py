import dataclasses
from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, assert_never, final

from fastapi import Depends
from trcks.oop import Wrapper

from subscription_management.data_structures.domain.do_not_update import (
    DO_NOT_UPDATE,
)
from subscription_management.data_structures.domain.product import (
    Product,
    ProductUpdate,
)
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

type _DeleteProductError = (
    ProductNotDeletableBecauseStatusError | ProductWithIdDoesNotExistError
)
type _UpdateNotAllowedError = (
    ProductPayloadNotUpdatableBecauseStatusError
    | ProductStatusTransitionNotAllowedError
)

type ProductServiceDep = Annotated[ProductService, Depends()]


@final
@dataclass(frozen=True, kw_only=True, slots=True)
class ProductService:
    _product_repository: ProductRepositoryDep

    @staticmethod
    def _delete_product(
        product: Product,
    ) -> Result[
        ProductNotDeletableBecauseStatusError,
        UUID,
    ]:
        if product.status == "draft":
            return "success", product.id
        return "failure", ProductNotDeletableBecauseStatusError(
            id=product.id, status=product.status
        )

    @staticmethod
    def _ensure_that_payload_update_is_allowed(
        before: Product, after: Product
    ) -> Result[ProductPayloadNotUpdatableBecauseStatusError, None]:
        if before.status == "draft":
            return "success", None

        payload_is_identical = before == dataclasses.replace(
            after, status=before.status
        )
        if payload_is_identical:
            return "success", None

        return "failure", ProductPayloadNotUpdatableBecauseStatusError(
            id=before.id, status=before.status
        )

    @staticmethod
    def _ensure_that_status_update_is_allowed(
        before: Product, after: Product
    ) -> Result[ProductStatusTransitionNotAllowedError, None]:
        match before.status, after.status:
            case (
                ("draft", "draft" | "published" | "deprecated")
                | ("published", "published" | "deprecated")
                | ("deprecated", "deprecated")
            ):
                return "success", None
            case ("published", "draft") | ("deprecated", "draft" | "published"):
                return "failure", ProductStatusTransitionNotAllowedError(
                    id=before.id,
                    before=before.status,
                    after=after.status,
                )
            case _ as status_update:  # pragma: no cover
                assert_never(status_update)  # pyright: ignore[reportUnreachable]

    @staticmethod
    def _merge_with_update(before: Product, update: ProductUpdate) -> Product:
        return Product(
            id=before.id,
            monthly_fee_in_euros=(
                before.monthly_fee_in_euros
                if update.monthly_fee_in_euros is DO_NOT_UPDATE
                else update.monthly_fee_in_euros
            ),
            name=(before.name if update.name is DO_NOT_UPDATE else update.name),
            status=(before.status if update.status is DO_NOT_UPDATE else update.status),
        )

    @classmethod
    def _update_product(
        cls, before: Product, update: ProductUpdate
    ) -> Result[_UpdateNotAllowedError, Product]:
        after = cls._merge_with_update(before, update)

        status_result = cls._ensure_that_status_update_is_allowed(before, after)
        if status_result[0] == "failure":
            return status_result

        payload_result = cls._ensure_that_payload_update_is_allowed(before, after)
        if payload_result[0] == "failure":
            return payload_result

        return "success", after

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
            .map_to_awaitable_result(self._product_repository.read_product_by_id)
            .map_success_to_result(self._delete_product)
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
        _UpdateNotAllowedError
        | ProductWithIdDoesNotExistError
        | ProductWithNameAlreadyExistsError,
        Product,
    ]:
        return (
            Wrapper(update.id)
            .map_to_awaitable_result(self._product_repository.read_product_by_id)
            .map_success_to_result(self._update_product, update=update)
            .map_success_to_awaitable_result(self._product_repository.update_product)
            .core
        )
