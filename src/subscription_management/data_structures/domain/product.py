import dataclasses
import enum
import functools
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


@functools.total_ordering
class ProductStatus(enum.Enum):
    """Statuses in lifecycle order."""

    DRAFT = "draft"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, ProductStatus):
            return NotImplemented
        statuses = tuple(ProductStatus)
        return statuses.index(self) < statuses.index(other)
