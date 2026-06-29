# pyright: reportUninitializedInstanceVariable=false
# See https://github.com/pydantic/pydantic/issues/10377#issuecomment-2342806423
from datetime import UTC, datetime
from typing import Literal, final

from pydantic import BaseModel, Field


@final
class HealthResponse(BaseModel, frozen=True):
    service: Literal["trcks-example-fastapi"] = "trcks-example-fastapi"
    status: Literal["healthy"] = "healthy"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
