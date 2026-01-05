import dataclasses
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from decimal import Decimal
    from uuid import UUID

type ProductStatus = Literal["draft", "published", "deprecated"]


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class Product:
    id: UUID
    monthly_fee_in_euros: Decimal
    name: str
    status: ProductStatus
