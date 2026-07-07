from typing import assert_never
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from trcks.oop import AwaitableTupleWrapper, Wrapper

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
from subscription_management.data_structures.schemas.product_schemas import (
    PostProductRequest,
    ProductResponse,
    PutProductRequest,
)
from subscription_management.logic.services.product_service import ProductServiceDep

product_router = APIRouter(prefix="/products", tags=["Products"])


@product_router.post(
    "/",
    responses={
        status.HTTP_409_CONFLICT: {
            "description": (
                "Conflict between product in request body and existing product "
                "(e.g. same name or ID)"
            )
        }
    },
    status_code=status.HTTP_201_CREATED,
)
async def create_product(
    post_product_request: PostProductRequest, product_service: ProductServiceDep
) -> ProductResponse:
    result = (
        await Wrapper(post_product_request)
        .map(PostProductRequest.to_product)
        .map_to_awaitable_result(product_service.create_product)
        .map_success(ProductResponse.from_product)
        .core
    )
    match result:
        case ("failure", ProductWithNameAlreadyExistsError(name=name)):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product with name {name} already exists.",
            )
        case ("failure", ProductWithIdAlreadyExistsError(id=id_)):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product with ID {id_} already exists.",
            )
        case ("success", product_response):
            return product_response
        case _:  # pragma: no cover
            assert_never(result)


@product_router.delete(
    "/{id_}",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Product not found"},
        status.HTTP_409_CONFLICT: {
            "description": (
                "Product cannot be deleted due to its status "
                "(e.g. published or deprecated)"
            )
        },
    },
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_product(id_: UUID, product_service: ProductServiceDep) -> None:
    result = await product_service.delete_product(id_)
    match result:
        case ("failure", ProductStatusDeprecatedError(id=id_from_err)):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Product with ID {id_from_err} cannot be deleted "
                    "because its status is deprecated."
                ),
            )
        case ("failure", ProductStatusPublishedError(id=id_from_err)):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Product with ID {id_from_err} cannot be deleted "
                    "because its status is published."
                ),
            )
        case ("failure", ProductWithIdDoesNotExistError(id=id_from_err)):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {id_from_err} does not exist.",
            )
        case ("success", _):
            return
        case _:  # pragma: no cover
            assert_never(result)


@product_router.get(
    "/by-name/{name}",
    responses={status.HTTP_404_NOT_FOUND: {"description": "Product not found"}},
)
async def read_product_by_name(
    name: str, product_service: ProductServiceDep
) -> ProductResponse:
    result = (
        await Wrapper(name)
        .map_to_awaitable_result(product_service.read_product_by_name)
        .map_success(ProductResponse.from_product)
        .core
    )
    match result:
        case ("failure", ProductWithNameDoesNotExistError(name=name_from_err)):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with name {name_from_err} does not exist.",
            )
        case ("success", product_response):
            return product_response
        case _:  # pragma: no cover
            assert_never(result)


@product_router.get(
    "/{id_}",
    responses={status.HTTP_404_NOT_FOUND: {"description": "Product not found"}},
)
async def read_product_by_id(
    id_: UUID, product_service: ProductServiceDep
) -> ProductResponse:
    result = (
        await Wrapper(id_)
        .map_to_awaitable_result(product_service.read_product_by_id)
        .map_success(ProductResponse.from_product)
        .core
    )
    match result:
        case ("failure", ProductWithIdDoesNotExistError(id=id_from_err)):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {id_from_err} does not exist.",
            )
        case ("success", product_response):
            return product_response
        case _:  # pragma: no cover
            assert_never(result)


@product_router.get("/")
async def read_products(
    product_service: ProductServiceDep,
) -> tuple[ProductResponse, ...]:
    return await (
        AwaitableTupleWrapper(product_service.read_products())
        .map(ProductResponse.from_product)
        .core
    )


@product_router.put(
    "/{id_}",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Product not found"},
        status.HTTP_409_CONFLICT: {
            "description": (
                "Conflict between product in request body and existing product "
                "(e.g. same name)"
            )
        },
    },
)
async def update_product(
    id_: UUID,
    put_product_request: PutProductRequest,
    product_service: ProductServiceDep,
) -> ProductResponse:
    result = (
        await Wrapper(id_)
        .map(put_product_request.to_product)
        .map_to_awaitable_result(product_service.update_product)
        .map_success(ProductResponse.from_product)
        .core
    )
    match result:
        case ("failure", ProductWithIdDoesNotExistError(id=id_from_err)):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {id_from_err} does not exist.",
            )
        case ("failure", ProductWithNameAlreadyExistsError(name=name)):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product with name '{name}' already exists.",
            )
        case (
            "failure",
            ProductPayloadUpdateError(reason=reason)
            | ProductStatusUpdateError(reason=reason),
        ):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=reason)
        case ("success", product_response):
            return product_response
        case _:  # pragma: no cover
            assert_never(result)
