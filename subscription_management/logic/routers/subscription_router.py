from typing import assert_never
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from trcks.oop import AwaitableTupleWrapper, Wrapper

from subscription_management.data_structures.domain.errors import (
    ProductDoesNotExistError,
    ProductInDeprecatedStatusError,
    ProductInDraftStatusError,
    SubscriptionDoesNotExistError,
    SubscriptionIdAlreadyExistsError,
    UserDoesNotExistError,
)
from subscription_management.data_structures.schemas.subscription_schemas import (
    PostSubscriptionRequest,
    PutSubscriptionRequest,
    SubscriptionResponse,
)
from subscription_management.logic.services.subscription_service import (
    SubscriptionServiceDep,
)

subscription_router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@subscription_router.post(
    "/",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "Not Found: user or product referenced does not exist"
        },
        status.HTTP_409_CONFLICT: {
            "description": (
                "Subscription ID already exists or "
                "product is in draft/deprecated status"
            )
        },
    },
    status_code=status.HTTP_201_CREATED,
)
async def create_subscription(
    post_subscription_request: PostSubscriptionRequest,
    subscription_service: SubscriptionServiceDep,
) -> SubscriptionResponse:
    result = (
        await Wrapper(post_subscription_request)
        .map(PostSubscriptionRequest.to_subscription_with_user_id_and_product_id)
        .map_to_awaitable_result(subscription_service.create_subscription)
        .map_success(SubscriptionResponse.from_subscription_with_product)
        .core
    )
    match result:
        case ("failure", SubscriptionIdAlreadyExistsError() as err):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Subscription with ID {err.id} already exists.",
            )
        case ("failure", UserDoesNotExistError() as err):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {err.id} does not exist.",
            )
        case ("failure", ProductDoesNotExistError() as err):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {err.id} does not exist.",
            )
        case ("failure", ProductInDraftStatusError() as err):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product with ID {err.id} is in draft status.",
            )
        case ("failure", ProductInDeprecatedStatusError() as err):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product with ID {err.id} is in deprecated status.",
            )
        case ("success", subscription_response):
            return subscription_response
        case _:  # pragma: no cover
            assert_never(result)


@subscription_router.delete(
    "/{id_}",
    responses={status.HTTP_404_NOT_FOUND: {"description": "Subscription Not Found"}},
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_subscription(
    id_: UUID, subscription_service: SubscriptionServiceDep
) -> None:
    result = await subscription_service.delete_subscription(id_)
    match result:
        case ("failure", SubscriptionDoesNotExistError() as err):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subscription with ID {err.id} does not exist.",
            )
        case ("success", _):
            return
        case _:  # pragma: no cover
            assert_never(result)


@subscription_router.get("/{id_}")
async def read_subscription_by_id(
    id_: UUID, subscription_service: SubscriptionServiceDep
) -> SubscriptionResponse:
    result = await subscription_service.read_subscription_by_id(id_)
    match result:
        case ("failure", SubscriptionDoesNotExistError() as err):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subscription with ID {err.id} does not exist.",
            )
        case ("success", payload):
            return SubscriptionResponse.from_subscription_with_product(payload)
        case _:  # pragma: no cover
            assert_never(result)


@subscription_router.get("/")
async def read_subscriptions(
    subscription_service: SubscriptionServiceDep,
) -> tuple[SubscriptionResponse, ...]:
    return await (
        AwaitableTupleWrapper(subscription_service.read_subscriptions())
        .map(SubscriptionResponse.from_subscription_with_product)
        .core
    )


@subscription_router.put(
    "/{id_}",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "Not Found: subscription, user, or product does not exist"
        },
        status.HTTP_409_CONFLICT: {
            "description": "Product is in draft/deprecated status"
        },
    },
)
async def update_subscription(
    id_: UUID,
    put_subscription_request: PutSubscriptionRequest,
    subscription_service: SubscriptionServiceDep,
) -> SubscriptionResponse:
    result = (
        await Wrapper(id_)
        .map(put_subscription_request.to_subscription_with_user_id_and_product_id)
        .map_to_awaitable_result(subscription_service.update_subscription)
        .map_success(SubscriptionResponse.from_subscription_with_product)
        .core
    )
    match result:
        case ("failure", SubscriptionDoesNotExistError() as err):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subscription with ID {err.id} does not exist.",
            )
        case ("failure", UserDoesNotExistError() as err):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {err.id} does not exist.",
            )
        case ("failure", ProductDoesNotExistError() as err):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {err.id} does not exist.",
            )
        case ("failure", ProductInDraftStatusError() as err):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product with ID {err.id} is in draft status.",
            )
        case ("failure", ProductInDeprecatedStatusError() as err):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product with ID {err.id} is in deprecated status.",
            )
        case ("success", subscription_response):
            return subscription_response
        case _:  # pragma: no cover
            assert_never(result)
