from datetime import UTC, datetime
from typing import Literal, TypedDict, final


@final
class HealthResponse(TypedDict):
    service: Literal["trcks-example-fastapi"]
    status: Literal["healthy"]
    timestamp: datetime


def create_health_response() -> HealthResponse:
    return {
        "service": "trcks-example-fastapi",
        "status": "healthy",
        "timestamp": datetime.now(UTC),
    }
