from fastapi import APIRouter

from subscription_management.data_structures.schemas.health_schemas import (
    HealthResponse,
    create_health_response,
)
from subscription_management.logic.services.dummy_service import DummyServiceDep

health_router = APIRouter(prefix="/health", tags=["Health"])


@health_router.get("/")
async def read_health(dummy_service: DummyServiceDep) -> HealthResponse:
    _ = await dummy_service.read_one()
    return create_health_response()
