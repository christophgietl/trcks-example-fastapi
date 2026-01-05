from fastapi import APIRouter

from app.data_structures.schemas.health_schemas import HealthResponse
from app.logic.services.dummy_service import DummyServiceDep

health_router = APIRouter(prefix="/health", tags=["Health"])


@health_router.get("/")
async def read_health(dummy_service: DummyServiceDep) -> HealthResponse:
    _ = await dummy_service.read_one()
    return HealthResponse()
