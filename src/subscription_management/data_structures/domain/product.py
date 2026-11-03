import dataclasses
import enum
from typing import TYPE_CHECKING, final

if TYPE_CHECKING:
    from decimal import Decimal
    from uuid import UUID


@final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class Product:
    id: UUID
    monthly_fee_in_euros: Decimal
    name: str
    status: ProductStatus


class ProductStatus(enum.Enum):
    DEPRECATED = "deprecated"
    DRAFT = "draft"
    PUBLISHED = "published"
