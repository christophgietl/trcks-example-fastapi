from typing import assert_never
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from trcks.oop import AwaitableTupleWrapper, Wrapper

from subscription_management.data_structures.domain.user_error import (
    UserWithEmailAlreadyExistsError,
    UserWithEmailDoesNotExistError,
    UserWithIdAlreadyExistsError,
    UserWithIdDoesNotExistError,
)
from subscription_management.data_structures.schemas.user_schemas import (
    PostUserRequest,
    PutUserRequest,
    UserResponse,
)
from subscription_management.logic.services.user_service import UserServiceDep

user_router = APIRouter(prefix="/users", tags=["Users"])


@user_router.post(
    "/",
    responses={
        status.HTTP_409_CONFLICT: {
            "description": (
                "Conflict between user in request body and existing user "
                "(e.g. same email or ID)"
            )
        }
    },
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    post_user_request: PostUserRequest, user_service: UserServiceDep
) -> UserResponse:
    result = (
        await Wrapper(post_user_request)
        .map(PostUserRequest.to_user)
        .map_to_awaitable_result(user_service.create_user)
        .map_success(UserResponse.from_user_with_subscriptions_with_products)
        .core
    )
    match result:
        case ("failure", UserWithEmailAlreadyExistsError(email=email)):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with email {email} already exists.",
            )
        case ("failure", UserWithIdAlreadyExistsError(id=id_)):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with ID {id_} already exists.",
            )
        case ("success", user_response):
            return user_response
        case _:  # pragma: no cover
            assert_never(result)  # pyright: ignore[reportUnreachable]


@user_router.delete(
    "/{id_}",
    description="Delete a user and all of their subscriptions.",
    responses={status.HTTP_404_NOT_FOUND: {"description": "User Not Found"}},
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user(id_: UUID, user_service: UserServiceDep) -> None:
    result = await user_service.delete_user(id_)
    match result:
        case ("failure", UserWithIdDoesNotExistError(id=id_from_err)):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {id_from_err} does not exist.",
            )
        case ("success", _):
            return
        case _:  # pragma: no cover
            assert_never(result)  # pyright: ignore[reportUnreachable]


@user_router.get(
    "/by-email/{email}",
    responses={status.HTTP_404_NOT_FOUND: {"description": "User Not Found"}},
    tags=["Products", "Subscriptions"],
)
async def read_user_by_email(email: str, user_service: UserServiceDep) -> UserResponse:
    result = (
        await Wrapper(email)
        .map_to_awaitable_result(user_service.read_user_by_email)
        .map_success(UserResponse.from_user_with_subscriptions_with_products)
        .core
    )
    match result:
        case ("failure", UserWithEmailDoesNotExistError(email=email_from_err)):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with email {email_from_err} does not exist.",
            )
        case ("success", user_response):
            return user_response
        case _:  # pragma: no cover
            assert_never(result)  # pyright: ignore[reportUnreachable]


@user_router.get(
    "/{id_}",
    responses={status.HTTP_404_NOT_FOUND: {"description": "User Not Found"}},
    tags=["Products", "Subscriptions"],
)
async def read_user_by_id(id_: UUID, user_service: UserServiceDep) -> UserResponse:
    result = (
        await Wrapper(id_)
        .map_to_awaitable_result(user_service.read_user_by_id)
        .map_success(UserResponse.from_user_with_subscriptions_with_products)
        .core
    )
    match result:
        case ("failure", UserWithIdDoesNotExistError(id=id_from_err)):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {id_from_err} does not exist.",
            )
        case ("success", user_response):
            return user_response
        case _:  # pragma: no cover
            assert_never(result)  # pyright: ignore[reportUnreachable]


@user_router.get("/", tags=["Products", "Subscriptions"])
async def read_users(user_service: UserServiceDep) -> tuple[UserResponse, ...]:
    return await (
        AwaitableTupleWrapper(user_service.read_users())
        .map(UserResponse.from_user_with_subscriptions_with_products)
        .core
    )


@user_router.put(
    "/{id_}",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "User Not Found"},
        status.HTTP_409_CONFLICT: {
            "description": (
                "Conflict between user in request body and existing user "
                "(e.g. same email)"
            )
        },
    },
    tags=["Products", "Subscriptions"],
)
async def update_user(
    id_: UUID, put_user_request: PutUserRequest, user_service: UserServiceDep
) -> UserResponse:
    result = (
        await Wrapper(id_)
        .map(put_user_request.to_user)
        .map_to_awaitable_result(user_service.update_user)
        .map_success(UserResponse.from_user_with_subscriptions_with_products)
        .core
    )
    match result:
        case ("failure", UserWithEmailAlreadyExistsError(email=email)):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with email {email} already exists.",
            )
        case ("failure", UserWithIdDoesNotExistError(id=id_from_err)):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {id_from_err} does not exist.",
            )
        case ("success", user_response):
            return user_response
        case _:  # pragma: no cover
            assert_never(result)  # pyright: ignore[reportUnreachable]
