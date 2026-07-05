import dataclasses
from decimal import Decimal
from typing import Literal, final
from uuid import UUID

type ProductStatus = Literal["draft", "published", "deprecated"]


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class Product:
    id: UUID
    monthly_fee_in_euros: Decimal
    name: str
    status: ProductStatus
