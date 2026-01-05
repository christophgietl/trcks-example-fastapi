from typing import assert_never
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from trcks.oop import Wrapper

from app.data_structures.schemas.product_schemas import (
    PostProductRequest,
    ProductResponse,
    PutProductRequest,
)
from app.logic.services.product_service import ProductServiceDep

product_router = APIRouter(prefix="/products", tags=["Products"])


def _get_product_cannot_be_deleted_detail(id_: UUID, status_: str) -> str:
    return f"Product with ID {id_} cannot be deleted because its status is {status_}."


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
) -> None:
    result = (
        await Wrapper(post_product_request)
        .map(PostProductRequest.to_product)
        .map_to_awaitable_result(product_service.create_product)
        .core
    )
    match result:
        case ("failure", "Name already exists"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product with name {post_product_request.name} already exists.",
            )
        case ("failure", "ID already exists"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product with ID {post_product_request.id} already exists.",
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
        case ("failure", "Product does not exist"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {id_} does not exist.",
            )
        case ("failure", "Product status is published"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=_get_product_cannot_be_deleted_detail(id_, "published"),
            )
        case ("failure", "Product status is deprecated"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=_get_product_cannot_be_deleted_detail(id_, "deprecated"),
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
        case ("failure", "Product does not exist"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with name {name} does not exist.",
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
        case ("failure", "Product does not exist"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {id_} does not exist.",
            )
        case ("success", product_response):
            return product_response
        case _:  # pragma: no cover
            assert_never(result)


@product_router.get("/")
async def read_products(
    product_service: ProductServiceDep,
) -> tuple[ProductResponse, ...]:
    products = await product_service.read_products()
    return tuple(ProductResponse.from_product(product) for product in products)


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
        case ("failure", "Product does not exist"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {id_} does not exist.",
            )
        case ("failure", "Name already exists"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Product with name '{put_product_request.name}' already exists."
                ),
            )
        case (
            "failure",
            "Cannot change status from published to draft"
            | "Cannot change status from deprecated to draft"
            | "Cannot change status from deprecated to published"
            | "Cannot modify non-status attributes of a published product"
            | "Cannot modify non-status attributes of a deprecated product" as detail,
        ):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)
        case ("success", product_response):
            return product_response
        case _:  # pragma: no cover
            assert_never(result)
